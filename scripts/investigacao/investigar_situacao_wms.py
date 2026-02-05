# -*- coding: utf-8 -*-
"""
Investiga códigos de situação do WMS e cruza com canhotos
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
    print("INVESTIGACAO: SITUACOES WMS E CRUZAMENTO COM CANHOTOS")
    print("=" * 70)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!")

    # 1. Buscar tabela de domínio de situações (TDDDOM ou similar)
    query1 = """
    SELECT TABLE_NAME
    FROM USER_TABLES
    WHERE TABLE_NAME LIKE '%SIT%'
       OR TABLE_NAME LIKE '%DOM%'
       OR TABLE_NAME LIKE 'TDD%'
    ORDER BY TABLE_NAME
    """
    r1 = executar_query(access_token, query1, "TABELAS DE DOMINIO/SITUACAO")
    if r1 and r1.get("rows"):
        print("\nTabelas encontradas:")
        for row in r1["rows"][:20]:
            print(f"  - {row[0]}")

    # 2. Verificar TDDDOM (Domínios)
    query2 = """
    SELECT NUCAMPO, VALOR, DESCRICAO
    FROM TDDDOM
    WHERE UPPER(DESCRICAO) LIKE '%RECEB%'
       OR UPPER(DESCRICAO) LIKE '%CONFER%'
       OR UPPER(DESCRICAO) LIKE '%ARMAZ%'
       OR UPPER(DESCRICAO) LIKE '%ENTRADA%'
       OR NUCAMPO IN (
           SELECT NUCAMPO FROM TDDCAM WHERE NOMETAB = 'TGWREC' AND NOMECAM = 'SITUACAO'
       )
    ORDER BY NUCAMPO, VALOR
    """
    r2 = executar_query(access_token, query2, "DOMINIOS DE SITUACAO WMS")
    if r2 and r2.get("rows"):
        print("\nDominios encontrados:")
        for row in r2["rows"]:
            print(f"  Campo {row[0]}, Valor {row[1]}: {row[2]}")

    # 3. Buscar o NUCAMPO da SITUACAO em TGWREC
    query3 = """
    SELECT NUCAMPO, NOMETAB, NOMECAM, DESCRCAMPO
    FROM TDDCAM
    WHERE NOMETAB = 'TGWREC' AND NOMECAM = 'SITUACAO'
    """
    r3 = executar_query(access_token, query3, "NUCAMPO DA SITUACAO EM TGWREC")
    if r3 and r3.get("rows"):
        nucampo = r3["rows"][0][0]
        print(f"\nNUCAMPO: {nucampo}")

        # Buscar domínios desse campo
        query3b = f"""
        SELECT VALOR, DESCRICAO
        FROM TDDDOM
        WHERE NUCAMPO = {nucampo}
        ORDER BY VALOR
        """
        r3b = executar_query(access_token, query3b, f"DOMINIOS DO NUCAMPO {nucampo}")
        if r3b and r3b.get("rows"):
            print("\nValores de SITUACAO em TGWREC:")
            for row in r3b["rows"]:
                print(f"  {row[0]}: {row[1]}")

    # 4. Ver se há uma view ou tabela com descrição das situações
    query4 = """
    SELECT COLUMN_NAME
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'VGWRECSITCAB'
    """
    r4 = executar_query(access_token, query4, "COLUNAS DE VGWRECSITCAB")
    if r4 and r4.get("rows"):
        print("\nColunas:")
        for row in r4["rows"]:
            print(f"  - {row[0]}")

    # 5. Verificar se há descrição em VGWRECSIT (pode ter mais colunas)
    query5 = """
    SELECT TABLE_NAME
    FROM USER_TABLES
    WHERE TABLE_NAME LIKE 'VGWREC%'
    """
    r5 = executar_query(access_token, query5, "VIEWS/TABELAS VGWREC*")
    if r5 and r5.get("rows"):
        print("\nTabelas/Views:")
        for row in r5["rows"]:
            print(f"  - {row[0]}")

    # 6. Cruzar canhotos com TGWREC para ver situações
    query6 = """
    SELECT
        rc.SEQRECCANH,
        rc.NUNOTA,
        rc.NUMNOTA,
        rc.DTRECEB,
        wms.SITUACAO,
        wms.STATUSCONF,
        wms.DTRECEBIMENTO,
        wms.CONFFINAL,
        CASE wms.SITUACAO
            WHEN 0 THEN 'Pendente'
            WHEN 1 THEN 'Aguardando'
            WHEN 2 THEN 'Em Recebimento'
            WHEN 3 THEN 'Em Conferencia'
            WHEN 4 THEN 'Conferido'
            WHEN 5 THEN 'Em Armazenagem'
            WHEN 6 THEN 'Armazenado'
            ELSE 'Desconhecido'
        END AS DESC_SITUACAO
    FROM AD_RECEBCANH rc
    LEFT JOIN TGWREC wms ON wms.NUNOTA = rc.NUNOTA
    ORDER BY rc.DTRECEB DESC
    """
    r6 = executar_query(access_token, query6, "CANHOTOS COM SITUACAO WMS")
    if r6 and r6.get("rows"):
        print(f"\n{len(r6['rows'])} registros encontrados")
        print("\nExemplos:")
        print(f"{'SEQ':>5} | {'NUNOTA':>8} | {'NF':>8} | {'SIT':>3} | {'CONF':>4} | DESCRICAO")
        print("-" * 70)
        for row in r6["rows"][:20]:
            print(f"{str(row[0]):>5} | {str(row[1]):>8} | {str(row[2]):>8} | {str(row[4]):>3} | {str(row[5]):>4} | {row[8]}")

    # 7. Estatísticas por situação
    query7 = """
    SELECT
        wms.SITUACAO,
        COUNT(*) AS QTD,
        CASE wms.SITUACAO
            WHEN 0 THEN 'Pendente'
            WHEN 1 THEN 'Aguardando'
            WHEN 2 THEN 'Em Recebimento'
            WHEN 3 THEN 'Em Conferencia'
            WHEN 4 THEN 'Conferido'
            WHEN 5 THEN 'Em Armazenagem'
            WHEN 6 THEN 'Armazenado'
            ELSE 'Desconhecido'
        END AS DESC_SITUACAO
    FROM AD_RECEBCANH rc
    LEFT JOIN TGWREC wms ON wms.NUNOTA = rc.NUNOTA
    GROUP BY wms.SITUACAO
    ORDER BY wms.SITUACAO
    """
    r7 = executar_query(access_token, query7, "ESTATISTICAS POR SITUACAO")
    if r7 and r7.get("rows"):
        print("\nEstatisticas:")
        for row in r7["rows"]:
            sit = row[0] if row[0] is not None else "NULL"
            print(f"  Situacao {sit}: {row[1]} canhotos - {row[2]}")

    print("\n" + "=" * 70)
    print("FIM DA INVESTIGACAO")
    print("=" * 70)

if __name__ == "__main__":
    main()
