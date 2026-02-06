"""
Script para descobrir quais colunas da TGFPAR contem um email especifico.
Busca no parceiro 210 todas as colunas que contem o email informado.
MMARRA DISTRIBUIDORA AUTOMOTIVA LTDA

Uso:
  python scripts/manutencao/descobrir_colunas_email.py
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

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

CODPARC_TESTE = 210
EMAIL_BUSCA = "nfe_grupocolorado@colorado.com.br"


def autenticar() -> bool:
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
        return False
    except Exception:
        return False


def executar_sql(sql: str):
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
        return None
    except Exception:
        return None


def main():
    print("=" * 60)
    print("DESCOBRIR COLUNAS DE EMAIL - TGFPAR")
    print(f"Parceiro: {CODPARC_TESTE}")
    print(f"Email buscado: {EMAIL_BUSCA}")
    print("=" * 60)

    print("\nAutenticando...")
    if not autenticar():
        print("❌ Falha na autenticacao!")
        return
    print("✅ Autenticado!")

    # Colunas candidatas com EMAIL no nome
    candidatas = [
        "EMAIL",
        "EMAILNFE",
        "EMAILNFSE",
        "EMAILENTREGA",
        "EMAILCOBRANCA",
        "EMAILNFCE",
        "EMAILNOTIFENTREGA",
        "AD_EMAILENTREGA",
        "AD_EMAILNOTIFENT",
        "AD_EMAIL",
        "AD_EMAILNFE",
        "AD_EMAILNFSE",
        "EMAILPEDVDA",
        "EMAILPEDCPA",
        "EMAILAVISO",
        "EMAILBOLETO",
    ]

    print(f"\n--- TESTANDO {len(candidatas)} COLUNAS ---\n")

    encontradas = []

    for coluna in candidatas:
        sql = f"SELECT {coluna} FROM TGFPAR WHERE CODPARC = {CODPARC_TESTE}"
        result = executar_sql(sql)

        if result is None:
            # Coluna nao existe
            continue

        rows = result.get("rows", [])
        valor = rows[0][0] if rows else None
        valor_str = str(valor or "").strip()

        if valor_str:
            tem_email = "✅" if EMAIL_BUSCA.lower() in valor_str.lower() else "  "
            print(f"  {tem_email} {coluna:<25} = {valor_str}")
            encontradas.append((coluna, valor_str))
        else:
            print(f"     {coluna:<25} = (vazio)")

    print(f"\n--- RESUMO ---")
    print(f"\nColunas que EXISTEM e tem o email '{EMAIL_BUSCA}':\n")

    for coluna, valor in encontradas:
        if EMAIL_BUSCA.lower() in valor.lower():
            print(f"  ✅ {coluna} = {valor}")

    print(f"\nUse esses nomes no script de replicacao!")
    print("=" * 60)


if __name__ == "__main__":
    main()
