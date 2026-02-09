"""
Script para REPLICAR emails no cadastro de parceiros (TGFPAR) do Sankhya
Copia EMAILNFE para EMAILNFSE, EMAIL e EMAILNOTIFENTREGA
MMARRA DISTRIBUIDORA AUTOMOTIVA LTDA

Uso:
  python scripts/manutencao/replicar_email_parceiros.py
"""

import os
import requests
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# Carregar .env do mcp_sankhya
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / "mcp_sankhya" / ".env")

# ============================================
# CONFIGURACAO
# ============================================
SANKHYA_CLIENT_ID = os.getenv("SANKHYA_CLIENT_ID", "")
SANKHYA_CLIENT_SECRET = os.getenv("SANKHYA_CLIENT_SECRET", "")
SANKHYA_X_TOKEN = os.getenv("SANKHYA_X_TOKEN", "")

AUTH_URL = "https://api.sankhya.com.br/authenticate"
BASE_URL = "https://api.sankhya.com.br/gateway/v1/mge/service.sbr"

ACCESS_TOKEN = ""

# Colunas
COLUNA_ORIGEM = "EMAILNFE"
COLUNA_DESTINO_NFSE = "EMAILNFSE"
COLUNA_DESTINO_EMAIL = "EMAIL"
COLUNA_DESTINO_ENTREGA = "EMAILNOTIFENTREGA"


def autenticar() -> bool:
    """Autentica na API Sankhya e obtem access_token"""
    global ACCESS_TOKEN

    try:
        response = requests.post(
            AUTH_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Token": SANKHYA_X_TOKEN
            },
            data={
                "client_id": SANKHYA_CLIENT_ID,
                "client_secret": SANKHYA_CLIENT_SECRET,
                "grant_type": "client_credentials"
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            ACCESS_TOKEN = data.get("access_token", "")
            if ACCESS_TOKEN:
                return True

        print(f"  HTTP {response.status_code}: {response.text[:200]}")
        return False
    except Exception as e:
        print(f"  Erro: {e}")
        return False


def executar_sql(sql: str):
    """Executa SQL na API Sankhya"""

    payload = {
        "serviceName": "DbExplorerSP.executeQuery",
        "requestBody": {"sql": sql}
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{BASE_URL}?serviceName=DbExplorerSP.executeQuery&outputType=json",
            headers=headers,
            json=payload,
            timeout=60
        )

        result = response.json()
        if result.get("status") == "1":
            return result.get("responseBody", {})
        else:
            print(f"  ❌ Erro API: {result.get('statusMessage', 'Erro desconhecido')}")
            return None
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return None


def buscar_parceiros() -> list:
    """Busca todos os parceiros que tem EMAILNFE preenchido (paginado com ROWNUM)"""

    # Primeiro contar quantos sao
    sql_count = (
        f"SELECT COUNT(*) FROM TGFPAR "
        f"WHERE {COLUNA_ORIGEM} IS NOT NULL "
        f"AND TRIM({COLUNA_ORIGEM}) IS NOT NULL"
    )
    result_count = executar_sql(sql_count)
    if result_count and result_count.get("rows"):
        total = result_count["rows"][0][0]
        print(f"  Total encontrado: {total}")
    else:
        print("  ❌ Nao foi possivel contar registros")
        return []

    # Buscar por faixas de CODPARC
    todos = []
    codparc_min = 0
    page_size = 5000

    while True:
        sql = (
            f"SELECT CODPARC, {COLUNA_ORIGEM} "
            f"FROM TGFPAR "
            f"WHERE {COLUNA_ORIGEM} IS NOT NULL "
            f"AND TRIM({COLUNA_ORIGEM}) IS NOT NULL "
            f"AND CODPARC > {codparc_min} "
            f"AND ROWNUM <= {page_size} "
            f"ORDER BY CODPARC"
        )

        result = executar_sql(sql)
        if not result or not result.get("rows"):
            break

        rows = result["rows"]
        todos.extend(rows)
        codparc_min = rows[-1][0]  # ultimo CODPARC da pagina
        print(f"  ... {len(todos)} parceiros carregados (ultimo CODPARC: {codparc_min})")

        if len(rows) < page_size:
            break

    return todos


def exportar_erros_excel(erros: list, filename: str = None):
    """Exporta a lista de erros para um arquivo Excel"""
    if not erros:
        print("\nNenhum erro para exportar.")
        return

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"erros_replicacao_emails_{timestamp}.xlsx"

    # Criar DataFrame
    df = pd.DataFrame(erros)

    # Salvar Excel
    output_dir = ROOT_DIR / "output" / "divergencias"
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename

    df.to_excel(filepath, index=False, sheet_name="Erros")

    print(f"\n📊 Excel gerado: {filepath}")
    return filepath


def atualizar_emails(codparc: int, email: str) -> tuple:
    """Atualiza os 3 campos de email usando CRUDServiceProvider.saveRecord"""

    payload = {
        "serviceName": "CRUDServiceProvider.saveRecord",
        "requestBody": {
            "dataSet": {
                "rootEntity": "Parceiro",
                "includePresentationFields": "S",
                "dataRow": {
                    "key": {
                        "CODPARC": {"$": str(codparc)}
                    },
                    "localFields": {
                        COLUNA_DESTINO_NFSE: {"$": str(email)},
                        COLUNA_DESTINO_EMAIL: {"$": str(email)},
                        COLUNA_DESTINO_ENTREGA: {"$": str(email)},
                    }
                },
                "entity": {
                    "fieldset": {
                        "list": f"CODPARC,NOMEPARC,{COLUNA_DESTINO_NFSE},{COLUNA_DESTINO_EMAIL},{COLUNA_DESTINO_ENTREGA}"
                    }
                }
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    max_tentativas = 3
    for tentativa in range(max_tentativas):
        try:
            response = requests.post(
                f"{BASE_URL}?serviceName=CRUDServiceProvider.saveRecord&outputType=json",
                headers=headers,
                json=payload,
                timeout=30
            )

            # Token expirou - renovar e tentar de novo
            if response.status_code == 401:
                print(" (renovando token...)", end="")
                if autenticar():
                    headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
                    continue
                else:
                    return False, "Falha ao renovar token"

            # Rate limit / Forbidden - aguardar e tentar novamente
            if response.status_code == 403:
                if tentativa < max_tentativas - 1:
                    wait_time = (tentativa + 1) * 2  # 2s, 4s
                    print(f" (403, aguardando {wait_time}s...)", end="")
                    time.sleep(wait_time)
                    continue
                else:
                    return False, f"HTTP 403 - Rate limit excedido"

            result = response.json()
            status = result.get("status", "0")

            if status == "1":
                entity = result.get("responseBody", {}).get("entities", {}).get("entity", {})
                nome = entity.get("NOMEPARC", {}).get("$", "")
                return True, nome
            else:
                msg = result.get("statusMessage") or result.get("message") or f"HTTP {response.status_code}"
                return False, msg

        except Exception as e:
            if tentativa < max_tentativas - 1:
                time.sleep(1)
                continue
            return False, str(e)

    return False, "Falha apos 3 tentativas"


def main():
    print("=" * 60)
    print("REPLICACAO DE EMAILS - TGFPAR - SANKHYA")
    print(f"Origem: {COLUNA_ORIGEM}")
    print(f"Destino: {COLUNA_DESTINO_NFSE}, {COLUNA_DESTINO_EMAIL}, {COLUNA_DESTINO_ENTREGA}")
    print("=" * 60)

    if not SANKHYA_CLIENT_ID or not SANKHYA_CLIENT_SECRET:
        print("\n❌ ERRO: Credenciais nao encontradas em mcp_sankhya/.env")
        return

    print("\nAutenticando na API Sankhya...")
    if not autenticar():
        print("❌ Falha na autenticacao!")
        return
    print("✅ Autenticado com sucesso!")

    # 1. Buscar parceiros
    print("\nBuscando parceiros com EMAILNFE preenchido...")
    parceiros = buscar_parceiros()

    if not parceiros:
        print("❌ Nenhum parceiro encontrado com EMAILNFE preenchido!")
        return

    print(f"✅ Encontrados: {len(parceiros)} parceiros")
    print("\n" + "-" * 60)

    # 2. Atualizar cada parceiro
    sucessos = 0
    erros = []

    for i, row in enumerate(parceiros, 1):
        codparc = row[0]
        email_raw = str(row[1]).strip()

        # Se tiver multiplos emails separados por ; usa so o primeiro
        email = email_raw.split(";")[0].strip()

        print(f"\n[{i:04d}/{len(parceiros)}] CODPARC: {codparc}", end="")

        sucesso, resultado = atualizar_emails(codparc, email)

        if sucesso:
            print(f" ✅ {resultado}")
            sucessos += 1
        else:
            print(f" ❌ {resultado}")
            erros.append({
                "CODPARC": codparc,
                "EMAIL_ORIGEM": email_raw,
                "EMAIL_USADO": email,
                "ERRO": resultado
            })

        time.sleep(0.5)  # Delay para evitar rate limit

    # 3. Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"✅ Atualizados: {sucessos}")
    print(f"❌ Erros: {len(erros)}")
    print(f"📊 Total: {len(parceiros)}")

    if erros:
        print("\n--- PRIMEIROS 10 ERROS ---")
        for e in erros[:10]:
            print(f"  - CODPARC {e['CODPARC']}: {e['ERRO']}")

        if len(erros) > 10:
            print(f"  ... e mais {len(erros) - 10} erros")

        # Exportar para Excel
        print("\n")
        exportar = input("Deseja exportar os erros para Excel? (s/n): ").strip().lower()
        if exportar == 's':
            exportar_erros_excel(erros)


if __name__ == "__main__":
    main()
