"""
Script de TESTE - Replica email de UM parceiro para validar
Copia EMAILNFE para EMAILNFSE, EMAIL e EMAIL de notificacao de entrega
MMARRA DISTRIBUIDORA AUTOMOTIVA LTDA

Uso:
  python scripts/manutencao/testar_replicar_email.py
"""

import os
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

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

# Parceiro para testar (o do screenshot: 210 - ACUCAR E ETANOL OSWALDO RIBEIRO DE MENDONCA S.A.)
CODPARC_TESTE = 210

# Colunas - ajuste se necessario
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


def executar_sql(sql: str) -> dict:
    """Executa SQL na API Sankhya e retorna o resultado completo"""

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
            timeout=30
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


def descobrir_colunas():
    """Testa cada coluna individualmente para descobrir os nomes corretos"""
    print("\n--- VERIFICANDO COLUNAS DE EMAIL ---")

    colunas = {
        COLUNA_ORIGEM: "E-mail p/ envio NF-e/NFS-e/CT-e (ORIGEM)",
        COLUNA_DESTINO_NFSE: "E-mail especifico p/ envio NFS-e",
        COLUNA_DESTINO_EMAIL: "Email (aba Endereco)",
        COLUNA_DESTINO_ENTREGA: "E-mail p/ notificacao de entrega",
    }

    todas_ok = True
    for coluna, descricao in colunas.items():
        sql = f"SELECT {coluna} FROM TGFPAR WHERE ROWNUM <= 1"
        result = executar_sql(sql)
        if result is not None:
            print(f"  ✅ {coluna:<20} -> {descricao}")
        else:
            print(f"  ❌ {coluna:<20} -> NAO EXISTE!")
            todas_ok = False

    if not todas_ok:
        # Buscar todas as colunas com EMAIL no nome para ajudar a descobrir
        print("\n--- COLUNAS COM 'EMAIL' NA TGFPAR ---")
        sql = "SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = 'TGFPAR' AND COLUMN_NAME LIKE '%EMAIL%' ORDER BY COLUMN_NAME"
        result = executar_sql(sql)
        if result and result.get("rows"):
            for row in result["rows"]:
                print(f"  - {row[0]}")
        else:
            # Alternativa caso USER_TAB_COLUMNS nao funcione
            print("  (Tentando busca alternativa...)")
            sql2 = "SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = 'TGFPAR' AND COLUMN_NAME LIKE '%EMAIL%' ORDER BY COLUMN_NAME"
            result2 = executar_sql(sql2)
            if result2 and result2.get("rows"):
                for row in result2["rows"]:
                    print(f"  - {row[0]}")

    return todas_ok


def consultar_emails(codparc: int) -> dict:
    """Consulta os campos de email atuais do parceiro"""

    sql = (
        f"SELECT CODPARC, NOMEPARC, "
        f"{COLUNA_ORIGEM}, {COLUNA_DESTINO_NFSE}, "
        f"{COLUNA_DESTINO_EMAIL}, {COLUNA_DESTINO_ENTREGA} "
        f"FROM TGFPAR WHERE CODPARC = {codparc}"
    )

    result = executar_sql(sql)
    if result:
        rows = result.get("rows", [])
        if rows:
            row = rows[0]
            return {
                "codparc": row[0],
                "nome": row[1],
                COLUNA_ORIGEM: row[2],
                COLUNA_DESTINO_NFSE: row[3],
                COLUNA_DESTINO_EMAIL: row[4],
                COLUNA_DESTINO_ENTREGA: row[5],
            }
    return None


def atualizar_emails(codparc: int, email: str) -> tuple:
    """Atualiza os 3 campos de email destino usando CRUDServiceProvider.saveRecord"""

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

    try:
        response = requests.post(
            f"{BASE_URL}?serviceName=CRUDServiceProvider.saveRecord&outputType=json",
            headers=headers,
            json=payload,
            timeout=30
        )

        result = response.json()
        status = result.get("status", "0")

        if status == "1":
            entity = result.get("responseBody", {}).get("entities", {}).get("entity", {})
            nome = entity.get("NOMEPARC", {}).get("$", "")
            return True, nome
        else:
            return False, result.get("statusMessage", "Erro desconhecido")

    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("TESTE - REPLICACAO DE EMAIL DE PARCEIRO")
    print(f"Parceiro de teste: CODPARC {CODPARC_TESTE}")
    print("=" * 60)

    if not SANKHYA_CLIENT_ID or not SANKHYA_CLIENT_SECRET:
        print("\n❌ ERRO: Credenciais nao encontradas em mcp_sankhya/.env")
        return

    print("\nAutenticando na API Sankhya...")
    if not autenticar():
        print("❌ Falha na autenticacao!")
        return
    print("✅ Autenticado com sucesso!")

    # 1. Verificar se as colunas existem
    if not descobrir_colunas():
        print("\n❌ Alguma coluna nao existe! Ajuste os nomes no topo do script (linhas 36-39)")
        return

    # 2. Consultar estado ANTES
    print("\n--- ESTADO ANTES ---")
    dados = consultar_emails(CODPARC_TESTE)

    if not dados:
        print(f"❌ Parceiro {CODPARC_TESTE} nao encontrado!")
        return

    print(f"  CODPARC:  {dados['codparc']}")
    print(f"  NOME:     {dados['nome']}")
    print(f"  {COLUNA_ORIGEM:<20} (origem):  {dados[COLUNA_ORIGEM] or '(vazio)'}")
    print(f"  {COLUNA_DESTINO_NFSE:<20} (dest 1):  {dados[COLUNA_DESTINO_NFSE] or '(vazio)'}")
    print(f"  {COLUNA_DESTINO_EMAIL:<20} (dest 2):  {dados[COLUNA_DESTINO_EMAIL] or '(vazio)'}")
    print(f"  {COLUNA_DESTINO_ENTREGA:<20} (dest 3):  {dados[COLUNA_DESTINO_ENTREGA] or '(vazio)'}")

    email_origem = dados[COLUNA_ORIGEM]
    if not email_origem or not str(email_origem).strip():
        print(f"\n❌ Campo {COLUNA_ORIGEM} esta vazio! Nao ha email para replicar.")
        return

    # 2. Executar atualizacao
    print(f"\n--- ATUALIZANDO ---")
    print(f"  Email a replicar: {email_origem}")

    sucesso, resultado = atualizar_emails(CODPARC_TESTE, email_origem)

    if sucesso:
        print(f"  ✅ Atualizado: {resultado}")
    else:
        print(f"  ❌ Erro: {resultado}")
        return

    time.sleep(0.5)

    # 3. Consultar estado DEPOIS
    print("\n--- ESTADO DEPOIS ---")
    dados_depois = consultar_emails(CODPARC_TESTE)

    if dados_depois:
        print(f"  CODPARC:  {dados_depois['codparc']}")
        print(f"  NOME:     {dados_depois['nome']}")
        print(f"  {COLUNA_ORIGEM:<20} (origem):  {dados_depois[COLUNA_ORIGEM] or '(vazio)'}")
        print(f"  {COLUNA_DESTINO_NFSE:<20} (dest 1):  {dados_depois[COLUNA_DESTINO_NFSE] or '(vazio)'}")
        print(f"  {COLUNA_DESTINO_EMAIL:<20} (dest 2):  {dados_depois[COLUNA_DESTINO_EMAIL] or '(vazio)'}")
        print(f"  {COLUNA_DESTINO_ENTREGA:<20} (dest 3):  {dados_depois[COLUNA_DESTINO_ENTREGA] or '(vazio)'}")

        # Verificar
        ok = (
            dados_depois[COLUNA_DESTINO_NFSE] == email_origem
            and dados_depois[COLUNA_DESTINO_EMAIL] == email_origem
            and dados_depois[COLUNA_DESTINO_ENTREGA] == email_origem
        )

        if ok:
            print("\n✅ TESTE OK! Todos os campos foram atualizados corretamente.")
            print("   Pode rodar o script completo:")
            print("   python scripts/manutencao/replicar_email_parceiros.py --executar")
        else:
            print("\n⚠️  Verifique os valores acima. Algum campo pode nao ter sido atualizado.")
            print("   Confira tambem direto no Sankhya.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
