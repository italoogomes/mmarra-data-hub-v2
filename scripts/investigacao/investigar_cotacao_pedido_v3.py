# -*- coding: utf-8 -*-
"""
Investiga a desconexao entre cotacao e empenho do pedido 1191930 - V3
"""

import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

NUNOTA_VENDA = 1191930

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
    print(f"INVESTIGACAO: DESCONEXAO COTACAO x EMPENHO - PEDIDO {NUNOTA_VENDA}")
    print("=" * 70)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!")

    # 1. O QUE SABEMOS:
    print("\n" + "=" * 70)
    print("RESUMO DO QUE SABEMOS:")
    print("=" * 70)
    print(f"""
    - Pedido de venda: {NUNOTA_VENDA}
    - Cotacao: 2385 (NUNOTAORIG = 1191931, nao 1191930)
    - Compra da cotacao: 1192265 (NF 1228) - SEM empenho!
    - Compra com empenho: 1193546 (NF 729637) - OUTRA compra!
    """)

    # 2. VER DETALHES DO NUNOTA 1191931 (origem da cotacao)
    query1 = """
    SELECT
        cab.NUNOTA,
        cab.NUMNOTA,
        cab.TIPMOV,
        cab.CODTIPOPER,
        top.DESCROPER,
        cab.CODPARC,
        par.NOMEPARC,
        cab.DTNEG,
        cab.VLRNOTA,
        cab.STATUSNOTA,
        cab.PENDENTE
    FROM TGFCAB cab
    LEFT JOIN TGFPAR par ON par.CODPARC = cab.CODPARC
    LEFT JOIN (
        SELECT CODTIPOPER, DESCROPER, ROW_NUMBER() OVER (PARTITION BY CODTIPOPER ORDER BY DHALTER DESC) RN
        FROM TGFTOP
    ) top ON top.CODTIPOPER = cab.CODTIPOPER AND top.RN = 1
    WHERE cab.NUNOTA = 1191931
    """
    r1 = executar_query(access_token, query1, "NUNOTA 1191931 (ORIGEM DA COTACAO 2385)")
    if r1 and r1.get("rows"):
        print("\nDados do NUNOTA 1191931:")
        fields = r1.get("fieldsMetadata", [])
        for i, field in enumerate(fields):
            valor = r1["rows"][0][i] if i < len(r1["rows"][0]) else None
            print(f"  {field['name']}: {valor}")

    # 3. COMPARAR AS DUAS COMPRAS
    query2 = """
    SELECT
        cab.NUNOTA,
        cab.NUMNOTA,
        cab.CODPARC,
        par.NOMEPARC,
        cab.DTNEG,
        cab.VLRNOTA,
        cab.CODTIPOPER,
        top.DESCROPER,
        cab.STATUSNOTA,
        cab.PENDENTE
    FROM TGFCAB cab
    LEFT JOIN TGFPAR par ON par.CODPARC = cab.CODPARC
    LEFT JOIN (
        SELECT CODTIPOPER, DESCROPER, ROW_NUMBER() OVER (PARTITION BY CODTIPOPER ORDER BY DHALTER DESC) RN
        FROM TGFTOP
    ) top ON top.CODTIPOPER = cab.CODTIPOPER AND top.RN = 1
    WHERE cab.NUNOTA IN (1192265, 1193546)
    ORDER BY cab.NUNOTA
    """
    r2 = executar_query(access_token, query2, "COMPARAR COMPRAS 1192265 vs 1193546")
    if r2 and r2.get("rows"):
        print("\n" + "-" * 100)
        print(f"{'NUNOTA':>10} | {'NUMNOTA':>10} | {'PARC':>6} | {'DATA':>12} | {'VALOR':>12} | {'TOP':>6} | {'ST':>3} | FORNECEDOR")
        print("-" * 100)
        for row in r2["rows"]:
            print(f"{str(row[0]):>10} | {str(row[1]):>10} | {str(row[2]):>6} | {str(row[4])[:12]:>12} | {str(row[5]):>12} | {str(row[6]):>6} | {str(row[8]):>3} | {str(row[3])[:30]}")

    # 4. VER ITENS DAS DUAS COMPRAS
    query3 = """
    SELECT
        ite.NUNOTA,
        ite.CODPROD,
        pro.DESCRPROD,
        ite.QTDNEG,
        ite.VLRUNIT,
        ite.VLRTOT
    FROM TGFITE ite
    LEFT JOIN TGFPRO pro ON pro.CODPROD = ite.CODPROD
    WHERE ite.NUNOTA IN (1192265, 1193546)
    ORDER BY ite.NUNOTA, ite.CODPROD
    """
    r3 = executar_query(access_token, query3, "ITENS DAS COMPRAS 1192265 E 1193546")
    if r3 and r3.get("rows"):
        print(f"\n{'NUNOTA':>10} | {'CODPROD':>8} | {'QTD':>6} | {'VLRUNIT':>10} | PRODUTO")
        print("-" * 90)
        for row in r3["rows"]:
            print(f"{str(row[0]):>10} | {str(row[1]):>8} | {str(row[3]):>6} | {str(row[4]):>10} | {str(row[2])[:35]}")

    # 5. VERIFICAR TODAS COTACOES DOS PRODUTOS DO PEDIDO 1191930
    query4 = """
    SELECT DISTINCT
        cot.NUMCOTACAO,
        cot.SITUACAO,
        cot.NUNOTAORIG,
        itc.CODPROD,
        pro.DESCRPROD,
        itc.NUNOTACPA,
        itc.STATUSPRODCOT,
        itc.MELHOR
    FROM TGFCOT cot
    JOIN TGFITC itc ON itc.NUMCOTACAO = cot.NUMCOTACAO
    LEFT JOIN TGFPRO pro ON pro.CODPROD = itc.CODPROD
    WHERE itc.CODPROD IN (406700, 10112)
    ORDER BY cot.NUMCOTACAO DESC, itc.CODPROD
    """
    r4 = executar_query(access_token, query4, "TODAS COTACOES DOS PRODUTOS 406700 E 10112")
    if r4 and r4.get("rows"):
        print(f"\n{'COT':>6} | {'SIT':>3} | {'ORIG':>10} | {'PROD':>8} | {'COMPRA':>10} | {'ST':>3} | {'MEL':>3} | PRODUTO")
        print("-" * 100)
        for row in r4["rows"]:
            print(f"{str(row[0]):>6} | {str(row[1]):>3} | {str(row[2]):>10} | {str(row[3]):>8} | {str(row[5]):>10} | {str(row[6]):>3} | {str(row[7]):>3} | {str(row[4])[:30]}")

    # 6. VERIFICAR RELACAO 1191930 vs 1191931 (sao pedidos seguidos?)
    query5 = """
    SELECT
        cab.NUNOTA,
        cab.NUMNOTA,
        cab.TIPMOV,
        cab.CODTIPOPER,
        cab.CODPARC,
        par.NOMEPARC,
        cab.DTNEG,
        cab.VLRNOTA
    FROM TGFCAB cab
    LEFT JOIN TGFPAR par ON par.CODPARC = cab.CODPARC
    WHERE cab.NUNOTA BETWEEN 1191929 AND 1191932
    ORDER BY cab.NUNOTA
    """
    r5 = executar_query(access_token, query5, "PEDIDOS PROXIMOS (1191929 a 1191932)")
    if r5 and r5.get("rows"):
        print(f"\n{'NUNOTA':>10} | {'NUMNOTA':>10} | {'TIP':>3} | {'TOP':>6} | {'DATA':>12} | {'VALOR':>12} | PARCEIRO")
        print("-" * 100)
        for row in r5["rows"]:
            print(f"{str(row[0]):>10} | {str(row[1]):>10} | {str(row[2]):>3} | {str(row[3]):>6} | {str(row[6])[:12]:>12} | {str(row[7]):>12} | {str(row[5])[:30]}")

    # 7. VER SE EXISTE ALGUM LOG/HISTORICO DE EMPENHO
    query6 = """
    SELECT * FROM (
        SELECT
            e.NUNOTAPEDVEN,
            e.NUNOTA AS NUNOTA_COMPRA,
            e.CODPROD,
            e.QTDEMPENHO,
            cab.NUMNOTA,
            cab.CODPARC,
            par.NOMEPARC,
            cab.DTNEG
        FROM TGWEMPE e
        LEFT JOIN TGFCAB cab ON cab.NUNOTA = e.NUNOTA
        LEFT JOIN TGFPAR par ON par.CODPARC = cab.CODPARC
        WHERE e.CODPROD = 406700
        ORDER BY e.NUNOTAPEDVEN DESC
    ) WHERE ROWNUM <= 10
    """
    r6 = executar_query(access_token, query6, "ULTIMOS EMPENHOS DO PRODUTO 406700")
    if r6 and r6.get("rows"):
        print(f"\n{'VENDA':>10} | {'COMPRA':>10} | {'PROD':>8} | {'QTD':>6} | {'NF':>10} | FORNECEDOR")
        print("-" * 90)
        for row in r6["rows"]:
            print(f"{str(row[0]):>10} | {str(row[1]):>10} | {str(row[2]):>8} | {str(row[3]):>6} | {str(row[4]):>10} | {str(row[6])[:30]}")

    print("\n" + "=" * 70)
    print("CONCLUSAO")
    print("=" * 70)

if __name__ == "__main__":
    main()
