# -*- coding: utf-8 -*-
"""
Investiga tabelas relacionadas a Recebimento de Canhoto
"""

import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

def autenticar():
    auth_response = requests.post(
        "https://api.sankhya.com.br/authenticate",
        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Token": X_TOKEN},
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
        timeout=30
    )
    if auth_response.status_code != 200:
        return None
    return auth_response.json()["access_token"]

def executar_query(access_token, query_sql, descricao=""):
    print(f"\n{'='*70}")
    print(f"[QUERY] {descricao}")
    print('='*70)
    query_payload = {"requestBody": {"sql": query_sql}}
    try:
        query_response = requests.post(
            "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=query_payload,
            timeout=60
        )
        if query_response.status_code != 200:
            print(f"[ERRO HTTP] {query_response.status_code}")
            return None
        result = query_response.json()
        if result.get("status") != "1":
            print(f"[ERRO] {result.get('statusMessage')}")
            return None
        return result.get("responseBody", {})
    except Exception as e:
        print(f"[ERRO] {e}")
        return None

def main():
    print("=" * 70)
    print("INVESTIGACAO: TABELAS DE RECEBIMENTO DE CANHOTO")
    print("=" * 70)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!")

    # 1. Buscar tabelas com CANHOTO no nome
    query1 = """
    SELECT TABLE_NAME
    FROM USER_TABLES
    WHERE TABLE_NAME LIKE '%CANHOTO%'
       OR TABLE_NAME LIKE '%CANHO%'
       OR TABLE_NAME LIKE '%REC%CANH%'
    ORDER BY TABLE_NAME
    """
    r1 = executar_query(access_token, query1, "TABELAS COM 'CANHOTO' NO NOME")
    if r1 and r1.get("rows"):
        print("\nTabelas encontradas:")
        for row in r1["rows"]:
            print(f"  - {row[0]}")
    else:
        print("\nNenhuma tabela com 'CANHOTO' no nome")

    # 2. Buscar tabelas AD_ (customizadas) que podem ter canhoto
    query2 = """
    SELECT TABLE_NAME
    FROM USER_TABLES
    WHERE TABLE_NAME LIKE 'AD_%'
      AND (TABLE_NAME LIKE '%CANH%' OR TABLE_NAME LIKE '%REC%' OR TABLE_NAME LIKE '%ENTREGA%')
    ORDER BY TABLE_NAME
    """
    r2 = executar_query(access_token, query2, "TABELAS AD_ RELACIONADAS")
    if r2 and r2.get("rows"):
        print("\nTabelas AD_ encontradas:")
        for row in r2["rows"]:
            print(f"  - {row[0]}")

    # 3. Buscar tabelas TGF com REC
    query3 = """
    SELECT TABLE_NAME
    FROM USER_TABLES
    WHERE TABLE_NAME LIKE 'TGF%REC%'
       OR TABLE_NAME LIKE 'TGFREC%'
    ORDER BY TABLE_NAME
    """
    r3 = executar_query(access_token, query3, "TABELAS TGF COM 'REC'")
    if r3 and r3.get("rows"):
        print("\nTabelas TGF com REC:")
        for row in r3["rows"]:
            print(f"  - {row[0]}")

    # 4. Verificar TGFREC (se existir)
    query4 = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFREC'
    ORDER BY COLUMN_ID
    """
    r4 = executar_query(access_token, query4, "ESTRUTURA DA TGFREC")
    if r4 and r4.get("rows"):
        print("\nColunas de TGFREC:")
        for row in r4["rows"][:30]:
            print(f"  - {row[0]}: {row[1]}")

    # 5. Buscar por SEQRECCANHOTO ou similar
    query5 = """
    SELECT TABLE_NAME, COLUMN_NAME
    FROM USER_TAB_COLUMNS
    WHERE COLUMN_NAME LIKE '%CANHOTO%'
       OR COLUMN_NAME LIKE '%SEQREC%'
    ORDER BY TABLE_NAME, COLUMN_NAME
    """
    r5 = executar_query(access_token, query5, "COLUNAS COM 'CANHOTO' OU 'SEQREC'")
    if r5 and r5.get("rows"):
        print("\nColunas encontradas:")
        for row in r5["rows"]:
            print(f"  - {row[0]}.{row[1]}")

    # 6. Tentar a tabela TGFRECCANHOTO diretamente
    query6 = """
    SELECT * FROM (
        SELECT * FROM TGFRECCANHOTO
        ORDER BY DHREC DESC
    ) WHERE ROWNUM <= 5
    """
    r6 = executar_query(access_token, query6, "DADOS DA TGFRECCANHOTO (TOP 5)")
    if r6 and r6.get("rows"):
        fields = r6.get("fieldsMetadata", [])
        print(f"\nColunas de TGFRECCANHOTO: {len(fields)}")
        for f in fields:
            print(f"  - {f['name']}")
        print(f"\nRegistros: {len(r6['rows'])}")

    # 7. Buscar tabelas com SEQ e REC
    query7 = """
    SELECT TABLE_NAME
    FROM USER_TABLES
    WHERE TABLE_NAME LIKE '%SEQ%REC%'
       OR TABLE_NAME LIKE '%REC%SEQ%'
    ORDER BY TABLE_NAME
    """
    r7 = executar_query(access_token, query7, "TABELAS COM SEQ E REC")
    if r7 and r7.get("rows"):
        print("\nTabelas com SEQ e REC:")
        for row in r7["rows"]:
            print(f"  - {row[0]}")

    print("\n" + "=" * 70)
    print("FIM DA INVESTIGACAO")
    print("=" * 70)

if __name__ == "__main__":
    main()
