# -*- coding: utf-8 -*-
"""
Investiga tabelas WMS para status de entrada, conferência e armazenagem
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
    print("INVESTIGACAO: STATUS WMS (ENTRADA/CONFERENCIA/ARMAZENAGEM)")
    print("=" * 70)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!")

    # 1. Ver estrutura da TGWREC (Recebimento WMS)
    query1 = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGWREC'
    ORDER BY COLUMN_ID
    """
    r1 = executar_query(access_token, query1, "ESTRUTURA DA TGWREC (Recebimento WMS)")
    if r1 and r1.get("rows"):
        print("\nColunas de TGWREC:")
        for row in r1["rows"]:
            print(f"  - {row[0]}: {row[1]}")

    # 2. Ver dados de exemplo da TGWREC
    query2 = """
    SELECT * FROM (
        SELECT
            r.NUNOTA,
            r.SITUACAO,
            r.DHINICIO,
            r.DHFIM,
            r.CODUSU,
            r.CODEMP
        FROM TGWREC r
        ORDER BY r.DHINICIO DESC
    ) WHERE ROWNUM <= 10
    """
    r2 = executar_query(access_token, query2, "DADOS DE TGWREC (TOP 10)")
    if r2 and r2.get("rows"):
        print("\nExemplos de TGWREC:")
        fields = r2.get("fieldsMetadata", [])
        for f in fields:
            print(f"  {f['name']}", end=" | ")
        print()
        for row in r2["rows"][:5]:
            print(f"  {row}")

    # 3. Ver valores distintos de SITUACAO em TGWREC
    query3 = """
    SELECT SITUACAO, COUNT(*) AS QTD
    FROM TGWREC
    GROUP BY SITUACAO
    ORDER BY QTD DESC
    """
    r3 = executar_query(access_token, query3, "VALORES DE SITUACAO EM TGWREC")
    if r3 and r3.get("rows"):
        print("\nSituacoes encontradas:")
        for row in r3["rows"]:
            print(f"  Situacao {row[0]}: {row[1]} registros")

    # 4. Buscar tabelas TGW relacionadas a conferencia/armazenagem
    query4 = """
    SELECT TABLE_NAME
    FROM USER_TABLES
    WHERE TABLE_NAME LIKE 'TGW%'
    ORDER BY TABLE_NAME
    """
    r4 = executar_query(access_token, query4, "TABELAS TGW (WMS)")
    if r4 and r4.get("rows"):
        print("\nTabelas TGW encontradas:")
        for row in r4["rows"]:
            print(f"  - {row[0]}")

    # 5. Ver estrutura da TGWARM (se existir - Armazenagem)
    query5 = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGWARM'
    ORDER BY COLUMN_ID
    """
    r5 = executar_query(access_token, query5, "ESTRUTURA DA TGWARM (Armazenagem)")
    if r5 and r5.get("rows"):
        print("\nColunas de TGWARM:")
        for row in r5["rows"]:
            print(f"  - {row[0]}: {row[1]}")

    # 6. Ver estrutura da TGWCON (se existir - Conferencia)
    query6 = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME LIKE 'TGWCON%'
    ORDER BY COLUMN_ID
    """
    r6 = executar_query(access_token, query6, "TABELAS TGWCON (Conferencia)")
    if r6 and r6.get("rows"):
        print("\nColunas encontradas:")
        for row in r6["rows"]:
            print(f"  - {row[0]}: {row[1]}")

    # 7. Cruzar com uma nota do canhoto para ver status
    query7 = """
    SELECT
        rc.SEQRECCANH,
        rc.NUNOTA,
        rc.NUMNOTA,
        rc.DTRECEB,
        wms.SITUACAO AS SITUACAO_WMS,
        wms.DHINICIO AS DH_INICIO_WMS,
        wms.DHFIM AS DH_FIM_WMS
    FROM AD_RECEBCANH rc
    LEFT JOIN TGWREC wms ON wms.NUNOTA = rc.NUNOTA
    WHERE ROWNUM <= 20
    ORDER BY rc.DTRECEB DESC
    """
    r7 = executar_query(access_token, query7, "CANHOTOS COM STATUS WMS")
    if r7 and r7.get("rows"):
        print("\nCanhotos com status WMS:")
        for row in r7["rows"]:
            print(f"  Seq {row[0]}, NF {row[2]}: Situacao WMS = {row[4]}")

    # 8. Verificar VGWRECSITCAB (View de situacao)
    query8 = """
    SELECT COLUMN_NAME
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'VGWRECSITCAB'
    ORDER BY COLUMN_ID
    """
    r8 = executar_query(access_token, query8, "ESTRUTURA DA VGWRECSITCAB (View Situacao)")
    if r8 and r8.get("rows"):
        print("\nColunas de VGWRECSITCAB:")
        for row in r8["rows"]:
            print(f"  - {row[0]}")

    # 9. Ver dados da view de situacao
    query9 = """
    SELECT * FROM (
        SELECT * FROM VGWRECSITCAB
        ORDER BY NUNOTA DESC
    ) WHERE ROWNUM <= 5
    """
    r9 = executar_query(access_token, query9, "DADOS DA VGWRECSITCAB")
    if r9 and r9.get("rows"):
        fields = r9.get("fieldsMetadata", [])
        print("\nColunas:", [f["name"] for f in fields])
        print("\nExemplos:")
        for row in r9["rows"]:
            print(f"  {row}")

    print("\n" + "=" * 70)
    print("FIM DA INVESTIGACAO")
    print("=" * 70)

if __name__ == "__main__":
    main()
