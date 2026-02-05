# -*- coding: utf-8 -*-
"""
Investiga se existe historico/log de cotacoes no Sankhya
"""

import os
import json
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
        print(f"[ERRO] {auth_response.text}")
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
    print("INVESTIGACAO DE HISTORICO DE COTACOES")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    # ========================================
    # QUERY 1: Buscar tabelas relacionadas a cotacao
    # ========================================
    query1 = """
    SELECT TABLE_NAME
    FROM ALL_TABLES
    WHERE TABLE_NAME LIKE '%COT%'
       OR TABLE_NAME LIKE '%COTACAO%'
       OR TABLE_NAME LIKE '%HIST%COT%'
       OR TABLE_NAME LIKE '%LOG%COT%'
    ORDER BY TABLE_NAME
    """
    result1 = executar_query(access_token, query1, "Tabelas relacionadas a cotacao")
    if result1 and result1.get("rows"):
        print("\nTabelas encontradas:")
        for row in result1["rows"]:
            print(f"  - {row[0]}")

    # ========================================
    # QUERY 2: Buscar tabelas de log/historico em geral
    # ========================================
    query2 = """
    SELECT TABLE_NAME
    FROM ALL_TABLES
    WHERE TABLE_NAME LIKE 'TSI%LOG%'
       OR TABLE_NAME LIKE 'TGF%LOG%'
       OR TABLE_NAME LIKE 'TGF%HIST%'
       OR TABLE_NAME LIKE '%AUDIT%'
    ORDER BY TABLE_NAME
    FETCH FIRST 30 ROWS ONLY
    """
    result2 = executar_query(access_token, query2, "Tabelas de log/historico gerais")
    if result2 and result2.get("rows"):
        print("\nTabelas de log/historico:")
        for row in result2["rows"]:
            print(f"  - {row[0]}")

    # ========================================
    # QUERY 3: Verificar se TGFCOT tem campo de alteracao
    # ========================================
    query3 = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFCOT'
      AND (COLUMN_NAME LIKE '%DT%' OR COLUMN_NAME LIKE '%DATA%' OR COLUMN_NAME LIKE '%ALTER%')
    ORDER BY COLUMN_ID
    """
    result3 = executar_query(access_token, query3, "Campos de data/alteracao em TGFCOT")
    if result3 and result3.get("rows"):
        print("\nCampos de data em TGFCOT:")
        for row in result3["rows"]:
            print(f"  - {row[0]} ({row[1]})")

    # ========================================
    # QUERY 4: Verificar tabela TSILOG (log geral do sistema)
    # ========================================
    query4 = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TSILOG'
    ORDER BY COLUMN_ID
    FETCH FIRST 20 ROWS ONLY
    """
    result4 = executar_query(access_token, query4, "Estrutura TSILOG (se existir)")
    if result4 and result4.get("rows"):
        print("\nColunas de TSILOG:")
        for row in result4["rows"]:
            print(f"  - {row[0]} ({row[1]})")

    # ========================================
    # QUERY 5: Ver se existe registro de log para cotacoes
    # ========================================
    query5 = """
    SELECT DISTINCT
        l.TABELA,
        l.EVENTO,
        COUNT(*) AS QTD
    FROM TSILOG l
    WHERE l.TABELA IN ('TGFCOT', 'TGFITC')
    GROUP BY l.TABELA, l.EVENTO
    ORDER BY l.TABELA, QTD DESC
    """
    result5 = executar_query(access_token, query5, "Logs existentes para TGFCOT/TGFITC")
    if result5 and result5.get("rows"):
        print("\nLogs encontrados:")
        print(f"{'TABELA':<15} | {'EVENTO':<15} | {'QTD':>10}")
        print("-" * 45)
        for row in result5["rows"]:
            print(f"{str(row[0]):<15} | {str(row[1]):<15} | {str(row[2]):>10}")
    else:
        print("\n[INFO] Nenhum log encontrado para tabelas de cotacao")

    # ========================================
    # QUERY 6: Verificar historico de alteracoes recentes
    # ========================================
    query6 = """
    SELECT
        cot.NUMCOTACAO,
        cot.DTALTER,
        cot.SITUACAO,
        cot.CODUSU
    FROM TGFCOT cot
    WHERE cot.DTALTER >= SYSDATE - 30
    ORDER BY cot.DTALTER DESC
    FETCH FIRST 20 ROWS ONLY
    """
    result6 = executar_query(access_token, query6, "Cotacoes alteradas nos ultimos 30 dias")
    if result6 and result6.get("rows"):
        print("\nCotacoes alteradas recentemente:")
        print(f"{'NUMCOT':>10} | {'DTALTER':<20} | {'SIT':<5} | {'CODUSU':>8}")
        print("-" * 55)
        for row in result6["rows"]:
            print(f"{str(row[0]):>10} | {str(row[1]):<20} | {str(row[2]):<5} | {str(row[3] or '-'):>8}")

    # ========================================
    # QUERY 7: Verificar se existe tabela de versoes
    # ========================================
    query7 = """
    SELECT TABLE_NAME
    FROM ALL_TABLES
    WHERE TABLE_NAME LIKE 'TGFCOT%'
       OR TABLE_NAME LIKE 'TGFITC%'
    ORDER BY TABLE_NAME
    """
    result7 = executar_query(access_token, query7, "Tabelas derivadas de TGFCOT/TGFITC")
    if result7 and result7.get("rows"):
        print("\nTabelas relacionadas:")
        for row in result7["rows"]:
            print(f"  - {row[0]}")

    # ========================================
    # QUERY 8: Evolucao de uma cotacao especifica
    # ========================================
    query8 = """
    SELECT
        cot.NUMCOTACAO,
        cot.DHINIC,
        cot.DHFINAL,
        cot.DTALTER,
        cot.SITUACAO,
        u.NOMEUSU AS RESPONSAVEL,
        (SELECT COUNT(*) FROM TGFITC itc WHERE itc.NUMCOTACAO = cot.NUMCOTACAO) AS QTD_ITENS,
        (SELECT COUNT(DISTINCT itc.CODPARC) FROM TGFITC itc WHERE itc.NUMCOTACAO = cot.NUMCOTACAO) AS QTD_FORNEC
    FROM TGFCOT cot
    LEFT JOIN TSIUSU u ON u.CODUSU = cot.CODUSURESP
    WHERE cot.SITUACAO = 'F'
    ORDER BY cot.NUMCOTACAO DESC
    FETCH FIRST 10 ROWS ONLY
    """
    result8 = executar_query(access_token, query8, "Cotacoes finalizadas (exemplo de ciclo)")
    if result8 and result8.get("rows"):
        print("\nCotacoes finalizadas:")
        print(f"{'NUMCOT':>8} | {'INICIO':<12} | {'FIM':<12} | {'SIT':<3} | {'ITENS':>6} | {'FORNEC':>6}")
        print("-" * 65)
        for row in result8["rows"]:
            inicio = str(row[1])[:10] if row[1] else '-'
            fim = str(row[2])[:10] if row[2] else '-'
            print(f"{str(row[0]):>8} | {inicio:<12} | {fim:<12} | {str(row[4]):<3} | {str(row[6]):>6} | {str(row[7]):>6}")

    print("\n" + "=" * 80)
    print("INVESTIGACAO CONCLUIDA!")
    print("=" * 80)

if __name__ == "__main__":
    main()
