# -*- coding: utf-8 -*-
"""
Investiga o contexto de uso dos status para entender significado
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
    print("CONTEXTO DOS STATUS DE COTACAO")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    # ========================================
    # QUERY 1: Correlacao STATUSPRODCOT com MELHOR
    # ========================================
    query1 = """
    SELECT
        itc.STATUSPRODCOT,
        itc.MELHOR,
        COUNT(*) AS QTD
    FROM TGFITC itc
    GROUP BY itc.STATUSPRODCOT, itc.MELHOR
    ORDER BY itc.STATUSPRODCOT, itc.MELHOR
    """
    result1 = executar_query(access_token, query1, "Relacao STATUSPRODCOT x MELHOR")
    if result1 and result1.get("rows"):
        print("\nResultado (STATUS x MELHOR):")
        print(f"{'STATUS':<10} | {'MELHOR':<8} | {'QTD':>10}")
        print("-" * 35)
        for row in result1["rows"]:
            print(f"{str(row[0]):<10} | {str(row[1]):<8} | {str(row[2]):>10}")

    # ========================================
    # QUERY 2: Correlacao SITUACAO com dados de cotacao
    # ========================================
    query2 = """
    SELECT
        cot.SITUACAO,
        CASE
            WHEN cot.DHINIC IS NOT NULL AND cot.DHFINAL IS NOT NULL THEN 'COM_PERIODO'
            WHEN cot.DHINIC IS NOT NULL THEN 'SO_INICIO'
            ELSE 'SEM_PERIODO'
        END AS TEM_PERIODO,
        COUNT(*) AS QTD
    FROM TGFCOT cot
    GROUP BY cot.SITUACAO,
        CASE
            WHEN cot.DHINIC IS NOT NULL AND cot.DHFINAL IS NOT NULL THEN 'COM_PERIODO'
            WHEN cot.DHINIC IS NOT NULL THEN 'SO_INICIO'
            ELSE 'SEM_PERIODO'
        END
    ORDER BY cot.SITUACAO
    """
    result2 = executar_query(access_token, query2, "Relacao SITUACAO x Periodo definido")
    if result2 and result2.get("rows"):
        print("\nResultado (SITUACAO x Periodo):")
        print(f"{'SITUACAO':<10} | {'PERIODO':<15} | {'QTD':>10}")
        print("-" * 40)
        for row in result2["rows"]:
            print(f"{str(row[0]):<10} | {str(row[1]):<15} | {str(row[2]):>10}")

    # ========================================
    # QUERY 3: Exemplo de itens com status O (mais comum)
    # ========================================
    query3 = """
    SELECT
        itc.NUMCOTACAO,
        itc.CODPROD,
        p.DESCRPROD,
        itc.STATUSPRODCOT,
        itc.MELHOR,
        itc.PRECO,
        itc.PRAZOENTREGA,
        itc.SITUACAO AS SIT_ITEM
    FROM TGFITC itc
    JOIN TGFPRO p ON p.CODPROD = itc.CODPROD
    WHERE itc.STATUSPRODCOT = 'O'
    ORDER BY itc.NUMCOTACAO DESC
    FETCH FIRST 10 ROWS ONLY
    """
    result3 = executar_query(access_token, query3, "Exemplos com status O (Orcamento?)")
    if result3 and result3.get("rows"):
        print("\nExemplos status O:")
        print(f"{'COT':>8} | {'PROD':>8} | {'MELHOR':<6} | {'PRECO':>12} | {'PRAZO':>6}")
        print("-" * 55)
        for row in result3["rows"]:
            print(f"{str(row[0]):>8} | {str(row[1]):>8} | {str(row[4]):<6} | {str(row[5] or 0):>12} | {str(row[6] or '-'):>6}")

    # ========================================
    # QUERY 4: Exemplo de itens com status F (segundo mais comum)
    # ========================================
    query4 = """
    SELECT
        itc.NUMCOTACAO,
        itc.CODPROD,
        itc.STATUSPRODCOT,
        itc.MELHOR,
        itc.PRECO,
        itc.NUNOTACPA,
        itc.SITUACAO AS SIT_ITEM
    FROM TGFITC itc
    WHERE itc.STATUSPRODCOT = 'F'
    ORDER BY itc.NUMCOTACAO DESC
    FETCH FIRST 10 ROWS ONLY
    """
    result4 = executar_query(access_token, query4, "Exemplos com status F (Finalizado?)")
    if result4 and result4.get("rows"):
        print("\nExemplos status F:")
        print(f"{'COT':>8} | {'PROD':>8} | {'MELHOR':<6} | {'PRECO':>12} | {'NUNOTACPA':>12}")
        print("-" * 55)
        for row in result4["rows"]:
            print(f"{str(row[0]):>8} | {str(row[1]):>8} | {str(row[3]):<6} | {str(row[4] or 0):>12} | {str(row[5] or '-'):>12}")

    # ========================================
    # QUERY 5: Itens marcados como MELHOR='S'
    # ========================================
    query5 = """
    SELECT
        itc.STATUSPRODCOT,
        COUNT(*) AS QTD,
        SUM(CASE WHEN itc.NUNOTACPA IS NOT NULL THEN 1 ELSE 0 END) AS COM_PEDIDO
    FROM TGFITC itc
    WHERE itc.MELHOR = 'S'
    GROUP BY itc.STATUSPRODCOT
    ORDER BY QTD DESC
    """
    result5 = executar_query(access_token, query5, "Itens marcados como MELHOR por status")
    if result5 and result5.get("rows"):
        print("\nItens MELHOR='S' por status:")
        print(f"{'STATUS':<10} | {'QTD':>10} | {'COM_PEDIDO':>12}")
        print("-" * 40)
        for row in result5["rows"]:
            print(f"{str(row[0]):<10} | {str(row[1]):>10} | {str(row[2]):>12}")

    # ========================================
    # QUERY 6: Verificar se C = Cancelado
    # ========================================
    query6 = """
    SELECT
        cot.SITUACAO,
        cot.OBSMOTCANC,
        cot.CODMOTCAN,
        COUNT(*) AS QTD
    FROM TGFCOT cot
    WHERE cot.SITUACAO = 'C'
    GROUP BY cot.SITUACAO, cot.OBSMOTCANC, cot.CODMOTCAN
    ORDER BY QTD DESC
    FETCH FIRST 10 ROWS ONLY
    """
    result6 = executar_query(access_token, query6, "Cotacoes com SITUACAO=C (tem motivo cancelamento?)")
    if result6 and result6.get("rows"):
        print("\nCotacoes SITUACAO=C:")
        print(f"{'SITUACAO':<10} | {'COD_MOT':>10} | {'QTD':>8} | {'OBS_MOT':<30}")
        print("-" * 65)
        for row in result6["rows"]:
            obs = str(row[1] or '')[:30]
            print(f"{str(row[0]):<10} | {str(row[2] or '-'):>10} | {str(row[3]):>8} | {obs:<30}")

    # ========================================
    # QUERY 7: Verificar pesos de criterios usados
    # ========================================
    query7 = """
    SELECT
        ROUND(AVG(NVL(PESOPRECO, 0)), 2) AS AVG_PRECO,
        ROUND(AVG(NVL(PESOCONDPAG, 0)), 2) AS AVG_CONDPAG,
        ROUND(AVG(NVL(PESOPRAZOENTREG, 0)), 2) AS AVG_PRAZO,
        ROUND(AVG(NVL(PESOQUALPROD, 0)), 2) AS AVG_QUALIDADE,
        ROUND(AVG(NVL(PESOCONFIABFORN, 0)), 2) AS AVG_CONFIAB,
        ROUND(AVG(NVL(PESOGARANTIA, 0)), 2) AS AVG_GARANTIA
    FROM TGFCOT
    WHERE SITUACAO = 'F'
    """
    result7 = executar_query(access_token, query7, "Media dos pesos de criterios (cotacoes finalizadas)")
    if result7 and result7.get("rows") and result7["rows"][0]:
        row = result7["rows"][0]
        print("\nMedia dos pesos (cotacoes finalizadas):")
        print(f"  Preco:        {row[0]}")
        print(f"  Cond.Pag:     {row[1]}")
        print(f"  Prazo Entreg: {row[2]}")
        print(f"  Qualidade:    {row[3]}")
        print(f"  Confiabil:    {row[4]}")
        print(f"  Garantia:     {row[5]}")

    print("\n" + "=" * 80)
    print("ANALISE CONCLUIDA!")
    print("=" * 80)

if __name__ == "__main__":
    main()
