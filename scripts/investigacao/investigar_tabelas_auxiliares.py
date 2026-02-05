# -*- coding: utf-8 -*-
"""
Investiga tabelas auxiliares de cotacao: TGFITC_COT, TGFITC_DLT, AD_COTACOESDEITENS
"""

import os
import requests
from dotenv import load_dotenv

# Carregar credenciais
env_path = os.path.join(os.path.dirname(__file__), 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

def autenticar():
    print("[1] Autenticando...")
    auth_response = requests.post(
        "https://api.sankhya.com.br/authenticate",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Token": X_TOKEN
        },
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
        },
        timeout=30
    )
    if auth_response.status_code != 200:
        return None
    print("[OK] Token obtido!")
    return auth_response.json()["access_token"]

def executar_query(access_token, query_sql, descricao):
    print(f"\n[QUERY] {descricao}")
    print("-" * 70)

    query_payload = {"requestBody": {"sql": query_sql}}
    query_response = requests.post(
        "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=query_payload,
        timeout=60
    )

    if query_response.status_code != 200:
        print(f"[ERRO] {query_response.text}")
        return None

    result = query_response.json()
    if result.get("status") != "1":
        print(f"[ERRO] {result.get('statusMessage')}")
        return None

    return result.get("responseBody", {})

def main():
    print("=" * 80)
    print("INVESTIGACAO DE TABELAS AUXILIARES DE COTACAO")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    # ========================================
    # QUERY 1: Estrutura TGFITC_COT
    # ========================================
    query1 = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFITC_COT'
    ORDER BY COLUMN_ID
    """
    result1 = executar_query(access_token, query1, "Estrutura TGFITC_COT")
    if result1 and result1.get("rows"):
        print("\nColunas de TGFITC_COT:")
        for row in result1["rows"]:
            print(f"  - {row[0]} ({row[1]})")

    # ========================================
    # QUERY 2: Contagem TGFITC_COT
    # ========================================
    query2 = """
    SELECT COUNT(*) AS TOTAL FROM TGFITC_COT
    """
    result2 = executar_query(access_token, query2, "Total registros TGFITC_COT")
    if result2 and result2.get("rows"):
        print(f"\nTotal: {result2['rows'][0][0]} registros")

    # ========================================
    # QUERY 3: Estrutura TGFITC_DLT
    # ========================================
    query3 = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFITC_DLT'
    ORDER BY COLUMN_ID
    """
    result3 = executar_query(access_token, query3, "Estrutura TGFITC_DLT")
    if result3 and result3.get("rows"):
        print("\nColunas de TGFITC_DLT:")
        for row in result3["rows"]:
            print(f"  - {row[0]} ({row[1]})")

    # ========================================
    # QUERY 4: Contagem TGFITC_DLT
    # ========================================
    query4 = """
    SELECT COUNT(*) AS TOTAL FROM TGFITC_DLT
    """
    result4 = executar_query(access_token, query4, "Total registros TGFITC_DLT")
    if result4 and result4.get("rows"):
        print(f"\nTotal: {result4['rows'][0][0]} registros")

    # ========================================
    # QUERY 5: Exemplo TGFITC_DLT (itens deletados)
    # ========================================
    query5 = """
    SELECT *
    FROM TGFITC_DLT
    ORDER BY NUMCOTACAO DESC
    FETCH FIRST 5 ROWS ONLY
    """
    result5 = executar_query(access_token, query5, "Exemplos TGFITC_DLT")
    if result5 and result5.get("rows"):
        fields = result5.get("fieldsMetadata", [])
        print("\nExemplos de itens deletados:")
        if fields:
            header = " | ".join([f["name"][:15] for f in fields[:6]])
            print(header)
            print("-" * 100)
        for row in result5["rows"]:
            values = " | ".join([str(v)[:15] for v in row[:6]])
            print(values)

    # ========================================
    # QUERY 6: Estrutura AD_COTACOESDEITENS
    # ========================================
    query6 = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'AD_COTACOESDEITENS'
    ORDER BY COLUMN_ID
    """
    result6 = executar_query(access_token, query6, "Estrutura AD_COTACOESDEITENS")
    if result6 and result6.get("rows"):
        print("\nColunas de AD_COTACOESDEITENS:")
        for row in result6["rows"]:
            print(f"  - {row[0]} ({row[1]})")

    # ========================================
    # QUERY 7: Contagem AD_COTACOESDEITENS
    # ========================================
    query7 = """
    SELECT COUNT(*) AS TOTAL FROM AD_COTACOESDEITENS
    """
    result7 = executar_query(access_token, query7, "Total registros AD_COTACOESDEITENS")
    if result7 and result7.get("rows"):
        print(f"\nTotal: {result7['rows'][0][0]} registros")

    # ========================================
    # QUERY 8: Estrutura TSICOT
    # ========================================
    query8 = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TSICOT'
    ORDER BY COLUMN_ID
    """
    result8 = executar_query(access_token, query8, "Estrutura TSICOT")
    if result8 and result8.get("rows"):
        print("\nColunas de TSICOT:")
        for row in result8["rows"]:
            print(f"  - {row[0]} ({row[1]})")

    # ========================================
    # QUERY 9: Contagem TSICOT
    # ========================================
    query9 = """
    SELECT COUNT(*) AS TOTAL FROM TSICOT
    """
    result9 = executar_query(access_token, query9, "Total registros TSICOT")
    if result9 and result9.get("rows"):
        print(f"\nTotal: {result9['rows'][0][0]} registros")

    print("\n" + "=" * 80)
    print("INVESTIGACAO CONCLUIDA!")
    print("=" * 80)

if __name__ == "__main__":
    main()
