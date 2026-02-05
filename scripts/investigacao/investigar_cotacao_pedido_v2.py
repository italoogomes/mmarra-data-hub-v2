# -*- coding: utf-8 -*-
"""
Investiga como a cotacao esta vinculada ao pedido de venda 1191930 - V2
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
    print(f"INVESTIGACAO DE COTACAO DO PEDIDO {NUNOTA_VENDA} - V2")
    print("=" * 70)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!")

    # 1. LISTAR TODOS OS CAMPOS DE TGFITC
    query1 = """
    SELECT COLUMN_NAME
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFITC'
    ORDER BY COLUMN_ID
    """
    r1 = executar_query(access_token, query1, "TODOS CAMPOS DE TGFITC")
    if r1 and r1.get("rows"):
        print("\nTodos os campos de TGFITC:")
        for row in r1["rows"]:
            print(f"  - {row[0]}")

    # 2. VERIFICAR COTACAO 2385 COM CAMPOS CORRETOS
    query2 = """
    SELECT
        itc.NUMCOTACAO,
        itc.CODPROD,
        itc.CODPARC,
        itc.STATUSPRODCOT,
        itc.MELHOR,
        itc.NUNOTACPA,
        itc.VLRUNIT,
        itc.VLRTOT,
        pro.DESCRPROD,
        par.NOMEPARC
    FROM TGFITC itc
    LEFT JOIN TGFPRO pro ON pro.CODPROD = itc.CODPROD
    LEFT JOIN TGFPAR par ON par.CODPARC = itc.CODPARC
    WHERE itc.NUMCOTACAO = 2385
    ORDER BY itc.CODPROD
    """
    r2 = executar_query(access_token, query2, "ITENS DA COTACAO 2385")
    if r2 and r2.get("rows"):
        print(f"\nItens da cotacao 2385: {len(r2['rows'])} registros")
        print(f"{'COT':>5} | {'PROD':>8} | {'PARC':>6} | {'ST':>3} | {'MEL':>3} | {'NUNOTACPA':>10} | PRODUTO")
        print("-" * 100)
        for row in r2["rows"]:
            print(f"{str(row[0]):>5} | {str(row[1]):>8} | {str(row[2]):>6} | {str(row[3]):>3} | {str(row[4]):>3} | {str(row[5]):>10} | {str(row[8])[:30]}")

    # 3. VER DADOS DA COTACAO 2385 COM NUNOTAORIG
    query3 = """
    SELECT
        cot.NUMCOTACAO,
        cot.SITUACAO,
        cot.NUNOTAORIG,
        cot.NUMNOTAORIG,
        cot.CODUSURESP,
        u.NOMEUSU,
        cot.DHINIC,
        cot.DHFINAL
    FROM TGFCOT cot
    LEFT JOIN TSIUSU u ON u.CODUSU = cot.CODUSURESP
    WHERE cot.NUMCOTACAO = 2385
    """
    r3 = executar_query(access_token, query3, "CABECALHO COTACAO 2385 (NUNOTAORIG)")
    if r3 and r3.get("rows"):
        print("\nDados da cotacao 2385:")
        fields = r3.get("fieldsMetadata", [])
        for i, field in enumerate(fields):
            valor = r3["rows"][0][i] if i < len(r3["rows"][0]) else None
            print(f"  {field['name']}: {valor}")

    # 4. BUSCAR COTACOES ONDE NUNOTAORIG = 1191930
    query4 = f"""
    SELECT
        cot.NUMCOTACAO,
        cot.SITUACAO,
        cot.NUNOTAORIG,
        cot.NUMNOTAORIG,
        u.NOMEUSU AS RESPONSAVEL
    FROM TGFCOT cot
    LEFT JOIN TSIUSU u ON u.CODUSU = cot.CODUSURESP
    WHERE cot.NUNOTAORIG = {NUNOTA_VENDA}
    """
    r4 = executar_query(access_token, query4, f"COTACOES COM NUNOTAORIG = {NUNOTA_VENDA}")
    if r4 and r4.get("rows"):
        print(f"\nCotacoes com NUNOTAORIG = {NUNOTA_VENDA}:")
        for row in r4["rows"]:
            print(f"  Cotacao {row[0]}: Situacao={row[1]}, NUNOTAORIG={row[2]}")
    else:
        print(f"\nNenhuma cotacao com NUNOTAORIG = {NUNOTA_VENDA}")

    # 5. VERIFICAR SE NUNOTACPA (em TGFITC) APONTA PARA COMPRA
    # E SE COMPRA TEM LINK COM VENDA
    query5 = """
    SELECT
        itc.NUMCOTACAO,
        itc.CODPROD,
        itc.NUNOTACPA,
        cab.NUMNOTA AS NF_COMPRA,
        cab.CODPARC AS FORNECEDOR,
        cab.CODTIPOPER
    FROM TGFITC itc
    LEFT JOIN TGFCAB cab ON cab.NUNOTA = itc.NUNOTACPA
    WHERE itc.NUMCOTACAO = 2385
      AND itc.NUNOTACPA IS NOT NULL
    """
    r5 = executar_query(access_token, query5, "COMPRAS GERADAS PELA COTACAO 2385")
    if r5 and r5.get("rows"):
        print(f"\nCompras geradas pela cotacao 2385:")
        for row in r5["rows"]:
            print(f"  Cotacao {row[0]}, Produto {row[1]} -> Compra NUNOTA={row[2]} (NF {row[3]})")

            # Verificar empenho dessa compra
            nunota_compra = row[2]
            if nunota_compra:
                query_empe = f"""
                SELECT
                    e.NUNOTAPEDVEN,
                    e.CODPROD,
                    e.QTDEMPENHO
                FROM TGWEMPE e
                WHERE e.NUNOTA = {nunota_compra}
                """
                r_empe = executar_query(access_token, query_empe, f"EMPENHO DA COMPRA {nunota_compra}")
                if r_empe and r_empe.get("rows"):
                    for empe in r_empe["rows"]:
                        print(f"    -> Empenhado para venda {empe[0]}, Produto {empe[1]}, Qtd {empe[2]}")

    # 6. VERIFICAR A COMPRA 1192265 (que aparece na screenshot)
    query6 = """
    SELECT
        cab.NUNOTA,
        cab.NUMNOTA,
        cab.CODPARC,
        par.NOMEPARC,
        cab.DTNEG,
        cab.VLRNOTA,
        cab.CODTIPOPER,
        cab.STATUSNOTA
    FROM TGFCAB cab
    LEFT JOIN TGFPAR par ON par.CODPARC = cab.CODPARC
    WHERE cab.NUNOTA = 1192265
    """
    r6 = executar_query(access_token, query6, "COMPRA 1192265 (da screenshot)")
    if r6 and r6.get("rows"):
        print("\nDados da compra 1192265:")
        fields = r6.get("fieldsMetadata", [])
        for i, field in enumerate(fields):
            valor = r6["rows"][0][i] if i < len(r6["rows"][0]) else None
            print(f"  {field['name']}: {valor}")

    # 7. EMPENHO DA COMPRA 1192265
    query7 = """
    SELECT
        e.NUNOTAPEDVEN,
        e.NUNOTA,
        e.CODPROD,
        e.QTDEMPENHO,
        pro.DESCRPROD
    FROM TGWEMPE e
    LEFT JOIN TGFPRO pro ON pro.CODPROD = e.CODPROD
    WHERE e.NUNOTA = 1192265
    """
    r7 = executar_query(access_token, query7, "EMPENHO DA COMPRA 1192265")
    if r7 and r7.get("rows"):
        print("\nEmpenhos da compra 1192265:")
        for row in r7["rows"]:
            print(f"  Venda {row[0]} <- Compra {row[1]}, Produto {row[2]}: {row[4]} ({row[3]} un)")
    else:
        print("\nNenhum empenho para compra 1192265")

    # 8. VERIFICAR SE TGFITC TEM CAMPO DE PEDIDO DE VENDA
    query8 = """
    SELECT COLUMN_NAME
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFITC'
      AND (COLUMN_NAME LIKE '%VENDA%' OR COLUMN_NAME LIKE '%PED%' OR COLUMN_NAME LIKE '%NUNOTA%')
    """
    r8 = executar_query(access_token, query8, "CAMPOS TGFITC RELACIONADOS A VENDA/PEDIDO")
    if r8 and r8.get("rows"):
        print("\nCampos em TGFITC que podem ter relacao com venda:")
        for row in r8["rows"]:
            print(f"  - {row[0]}")

    print("\n" + "=" * 70)
    print("CONCLUSAO")
    print("=" * 70)

if __name__ == "__main__":
    main()
