# -*- coding: utf-8 -*-
"""
Investiga os status de cotacao no Sankhya
Descobre todos os valores possiveis de STATUSPRODCOT e SITUACAO
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
    """Obtem token de acesso"""
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
        print(f"[ERRO] Autenticacao falhou: {auth_response.text}")
        return None

    access_token = auth_response.json()["access_token"]
    print("[OK] Token obtido!")
    return access_token

def executar_query(access_token, query_sql, descricao):
    """Executa uma query e retorna os resultados"""
    print(f"\n[QUERY] {descricao}")
    print("-" * 60)

    query_payload = {
        "requestBody": {
            "sql": query_sql
        }
    }

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
        print(f"[ERRO] Query falhou: {query_response.text}")
        return None

    result = query_response.json()

    if result.get("status") != "1":
        print(f"[ERRO] {result.get('statusMessage')}")
        return None

    response_body = result.get("responseBody", {})
    fields = response_body.get("fieldsMetadata", [])
    rows = response_body.get("rows", [])

    return {"fields": fields, "rows": rows}

def main():
    print("=" * 80)
    print("INVESTIGACAO DE STATUS DE COTACAO - SANKHYA")
    print("=" * 80)

    # Autenticar
    access_token = autenticar()
    if not access_token:
        return

    resultados = {}

    # ========================================
    # QUERY 1: Status do Produto na Cotacao (TGFITC.STATUSPRODCOT)
    # ========================================
    query1 = """
    SELECT
        STATUSPRODCOT AS STATUS,
        COUNT(*) AS QTD,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS PERCENTUAL
    FROM TGFITC
    WHERE STATUSPRODCOT IS NOT NULL
    GROUP BY STATUSPRODCOT
    ORDER BY QTD DESC
    """

    result1 = executar_query(access_token, query1, "Status do Produto na Cotacao (TGFITC.STATUSPRODCOT)")
    if result1 and result1["rows"]:
        print("\nValores encontrados:")
        print(f"{'STATUS':<10} | {'QTD':>10} | {'%':>8}")
        print("-" * 35)
        for row in result1["rows"]:
            print(f"{str(row[0]):<10} | {str(row[1]):>10} | {str(row[2]):>7}%")
        resultados["STATUSPRODCOT"] = result1["rows"]

    # ========================================
    # QUERY 2: Situacao da Cotacao (TGFCOT.SITUACAO)
    # ========================================
    query2 = """
    SELECT
        SITUACAO AS STATUS,
        COUNT(*) AS QTD,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS PERCENTUAL
    FROM TGFCOT
    WHERE SITUACAO IS NOT NULL
    GROUP BY SITUACAO
    ORDER BY QTD DESC
    """

    result2 = executar_query(access_token, query2, "Situacao da Cotacao (TGFCOT.SITUACAO)")
    if result2 and result2["rows"]:
        print("\nValores encontrados:")
        print(f"{'STATUS':<10} | {'QTD':>10} | {'%':>8}")
        print("-" * 35)
        for row in result2["rows"]:
            print(f"{str(row[0]):<10} | {str(row[1]):>10} | {str(row[2]):>7}%")
        resultados["SITUACAO_COTACAO"] = result2["rows"]

    # ========================================
    # QUERY 3: Colunas da tabela TGFCOT
    # ========================================
    query3 = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFCOT'
    ORDER BY COLUMN_ID
    """

    result3 = executar_query(access_token, query3, "Estrutura da tabela TGFCOT")
    if result3 and result3["rows"]:
        print("\nColunas da TGFCOT:")
        print(f"{'COLUNA':<25} | {'TIPO':<15} | {'TAM':>6} | {'NULL':<5}")
        print("-" * 60)
        for row in result3["rows"]:
            print(f"{str(row[0]):<25} | {str(row[1]):<15} | {str(row[2]):>6} | {str(row[3]):<5}")
        resultados["COLUNAS_TGFCOT"] = result3["rows"]

    # ========================================
    # QUERY 4: Colunas da tabela TGFITC
    # ========================================
    query4 = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFITC'
    ORDER BY COLUMN_ID
    """

    result4 = executar_query(access_token, query4, "Estrutura da tabela TGFITC")
    if result4 and result4["rows"]:
        print("\nColunas da TGFITC:")
        print(f"{'COLUNA':<25} | {'TIPO':<15} | {'TAM':>6} | {'NULL':<5}")
        print("-" * 60)
        for row in result4["rows"]:
            print(f"{str(row[0]):<25} | {str(row[1]):<15} | {str(row[2]):>6} | {str(row[3]):<5}")
        resultados["COLUNAS_TGFITC"] = result4["rows"]

    # ========================================
    # QUERY 5: Exemplo de cotacoes recentes com detalhes
    # ========================================
    query5 = """
    SELECT
        cot.NUMCOTACAO,
        cot.SITUACAO,
        cot.DTCOTACAO,
        u.NOMEUSU AS RESPONSAVEL,
        (SELECT COUNT(*) FROM TGFITC itc WHERE itc.NUMCOTACAO = cot.NUMCOTACAO) AS QTD_ITENS
    FROM TGFCOT cot
    LEFT JOIN TSIUSU u ON u.CODUSU = cot.CODUSURESP
    WHERE cot.DTCOTACAO >= ADD_MONTHS(SYSDATE, -6)
    ORDER BY cot.DTCOTACAO DESC
    FETCH FIRST 20 ROWS ONLY
    """

    result5 = executar_query(access_token, query5, "Cotacoes recentes (ultimos 6 meses)")
    if result5 and result5["rows"]:
        print("\nCotacoes recentes:")
        print(f"{'NUMCOT':>10} | {'SIT':<5} | {'DATA':<12} | {'RESPONSAVEL':<25} | {'ITENS':>6}")
        print("-" * 70)
        for row in result5["rows"]:
            print(f"{str(row[0]):>10} | {str(row[1]):<5} | {str(row[2])[:10]:<12} | {str(row[3] or '')[:25]:<25} | {str(row[4]):>6}")
        resultados["COTACOES_RECENTES"] = result5["rows"]

    # ========================================
    # QUERY 6: Status do item por cotacao (detalhado)
    # ========================================
    query6 = """
    SELECT
        itc.NUMCOTACAO,
        itc.CODPROD,
        p.DESCRPROD,
        itc.CODPARC,
        par.NOMEPARC AS FORNECEDOR,
        itc.STATUSPRODCOT,
        itc.VLRUNIT,
        itc.QTDCOT
    FROM TGFITC itc
    JOIN TGFPRO p ON p.CODPROD = itc.CODPROD
    JOIN TGFPAR par ON par.CODPARC = itc.CODPARC
    WHERE itc.NUMCOTACAO IN (
        SELECT NUMCOTACAO FROM TGFCOT
        WHERE DTCOTACAO >= ADD_MONTHS(SYSDATE, -3)
        ORDER BY DTCOTACAO DESC
        FETCH FIRST 5 ROWS ONLY
    )
    ORDER BY itc.NUMCOTACAO DESC, itc.CODPROD
    FETCH FIRST 30 ROWS ONLY
    """

    result6 = executar_query(access_token, query6, "Itens de cotacoes recentes (detalhado)")
    if result6 and result6["rows"]:
        print("\nItens de cotacoes:")
        print(f"{'NUMCOT':>8} | {'PROD':>8} | {'STATUS':<8} | {'VLRUNIT':>12} | {'FORNECEDOR':<25}")
        print("-" * 75)
        for row in result6["rows"]:
            print(f"{str(row[0]):>8} | {str(row[1]):>8} | {str(row[5]):<8} | {str(row[6]):>12} | {str(row[4] or '')[:25]:<25}")
        resultados["ITENS_COTACAO"] = result6["rows"]

    # ========================================
    # Salvar resultados
    # ========================================
    print("\n" + "=" * 80)
    print("SALVANDO RESULTADOS...")

    output_file = "resultado_investigacao_status.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)
    print(f"[OK] Resultados salvos em: {output_file}")

    print("\n" + "=" * 80)
    print("INVESTIGACAO CONCLUIDA!")
    print("=" * 80)

if __name__ == "__main__":
    main()
