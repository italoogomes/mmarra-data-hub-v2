# -*- coding: utf-8 -*-
"""
Investiga como a cotacao esta vinculada ao pedido de venda 1191930
"""

import os
import requests
from dotenv import load_dotenv

# Subir 2 niveis (scripts/investigacao -> raiz) e entrar em mcp_sankhya
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

NUNOTA_VENDA = 1191930  # Pedido a investigar

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
    print(f"INVESTIGACAO DE COTACAO DO PEDIDO {NUNOTA_VENDA}")
    print("=" * 70)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!")

    # 1. BUSCAR ITENS DO PEDIDO DE VENDA
    query1 = f"""
    SELECT i.CODPROD, p.DESCRPROD, i.QTDNEG
    FROM TGFITE i
    LEFT JOIN TGFPRO p ON p.CODPROD = i.CODPROD
    WHERE i.NUNOTA = {NUNOTA_VENDA}
    """
    r1 = executar_query(access_token, query1, "ITENS DO PEDIDO DE VENDA")
    produtos = []
    if r1 and r1.get("rows"):
        print(f"\nProdutos do pedido {NUNOTA_VENDA}:")
        for row in r1["rows"]:
            print(f"  - {row[0]}: {row[1]} (Qtd: {row[2]})")
            produtos.append(row[0])

    # 2. VER ESTRUTURA DA TABELA TGFITC (item de cotacao)
    query2 = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFITC'
    ORDER BY COLUMN_ID
    """
    r2 = executar_query(access_token, query2, "ESTRUTURA DA TABELA TGFITC")
    if r2 and r2.get("rows"):
        print(f"\nCampos da tabela TGFITC:")
        campos_interesse = ['NUNOTA', 'NUNOTAPED', 'NUNOTAPEDVEN', 'NUNOTAVENDA', 'CODPROD', 'CODPARC', 'NUMCOTACAO']
        for row in r2["rows"]:
            campo = row[0]
            tipo = row[1]
            # Destacar campos que parecem ter relacao com pedido
            if any(x in campo.upper() for x in ['NUNOTA', 'PED', 'VENDA', 'COMPRA']):
                print(f"  >>> {campo}: {tipo}")
            elif campo in campos_interesse:
                print(f"  * {campo}: {tipo}")

    # 3. BUSCAR COTACOES QUE MENCIONAM O PEDIDO 1191930
    query3 = f"""
    SELECT DISTINCT
        itc.NUMCOTACAO,
        itc.CODPROD,
        itc.CODPARC,
        itc.STATUSPRODCOT,
        itc.MELHOR,
        itc.NUNOTACOMPRA,
        par.NOMEPARC AS FORNECEDOR
    FROM TGFITC itc
    LEFT JOIN TGFPAR par ON par.CODPARC = itc.CODPARC
    WHERE itc.CODPROD IN ({','.join(str(p) for p in produtos)})
    ORDER BY itc.NUMCOTACAO DESC, itc.CODPROD
    """
    r3 = executar_query(access_token, query3, "COTACOES DOS PRODUTOS DO PEDIDO")
    if r3 and r3.get("rows"):
        print(f"\nCotacoes encontradas para os produtos:")
        print(f"{'COTACAO':>8} | {'PROD':>8} | {'PARC':>6} | {'ST':>3} | {'MEL':>3} | {'COMPRA':>10} | FORNECEDOR")
        print("-" * 90)
        for row in r3["rows"][:20]:
            print(f"{str(row[0]):>8} | {str(row[1]):>8} | {str(row[2]):>6} | {str(row[3]):>3} | {str(row[4]):>3} | {str(row[5]):>10} | {str(row[6])[:30]}")

    # 4. BUSCAR NA TGFCOT (cabecalho de cotacao) - procurar campo que liga ao pedido de venda
    query4 = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFCOT'
    ORDER BY COLUMN_ID
    """
    r4 = executar_query(access_token, query4, "ESTRUTURA DA TABELA TGFCOT")
    if r4 and r4.get("rows"):
        print(f"\nCampos da tabela TGFCOT que podem ter relacao com pedido:")
        for row in r4["rows"]:
            campo = row[0]
            tipo = row[1]
            if any(x in campo.upper() for x in ['NUNOTA', 'PED', 'VENDA', 'COMPRA', 'ORIG']):
                print(f"  >>> {campo}: {tipo}")

    # 5. VERIFICAR A COTACAO 2385 ESPECIFICAMENTE
    query5 = """
    SELECT
        cot.NUMCOTACAO,
        cot.SITUACAO,
        cot.DHINIC,
        cot.DHFINAL,
        cot.CODUSURESP,
        u.NOMEUSU AS RESPONSAVEL,
        cot.OBSERVACAO
    FROM TGFCOT cot
    LEFT JOIN TSIUSU u ON u.CODUSU = cot.CODUSURESP
    WHERE cot.NUMCOTACAO = 2385
    """
    r5 = executar_query(access_token, query5, "DADOS DA COTACAO 2385")
    if r5 and r5.get("rows"):
        print("\nDados da cotacao 2385:")
        fields = r5.get("fieldsMetadata", [])
        for i, field in enumerate(fields):
            valor = r5["rows"][0][i] if i < len(r5["rows"][0]) else None
            print(f"  {field['name']}: {valor}")

    # 6. ITENS DA COTACAO 2385
    query6 = """
    SELECT
        itc.NUMCOTACAO,
        itc.SEQUENCIA,
        itc.CODPROD,
        pro.DESCRPROD,
        itc.CODPARC,
        par.NOMEPARC AS FORNECEDOR,
        itc.STATUSPRODCOT,
        itc.MELHOR,
        itc.NUNOTACOMPRA,
        itc.VLRUNIT,
        itc.VLRTOT
    FROM TGFITC itc
    LEFT JOIN TGFPRO pro ON pro.CODPROD = itc.CODPROD
    LEFT JOIN TGFPAR par ON par.CODPARC = itc.CODPARC
    WHERE itc.NUMCOTACAO = 2385
    ORDER BY itc.CODPROD, itc.SEQUENCIA
    """
    r6 = executar_query(access_token, query6, "ITENS DA COTACAO 2385")
    if r6 and r6.get("rows"):
        print(f"\nItens da cotacao 2385: {len(r6['rows'])} registros")
        print(f"{'SEQ':>4} | {'PROD':>8} | {'PARC':>6} | {'ST':>3} | {'MEL':>3} | {'COMPRA':>10} | {'VLRUNIT':>10} | FORNECEDOR")
        print("-" * 100)
        for row in r6["rows"]:
            print(f"{str(row[1]):>4} | {str(row[2]):>8} | {str(row[4]):>6} | {str(row[6]):>3} | {str(row[7]):>3} | {str(row[8]):>10} | {str(row[9]):>10} | {str(row[5])[:25]}")

    # 7. VERIFICAR SE EXISTE CAMPO QUE LIGA COTACAO AO PEDIDO DE VENDA
    # Pode ser atraves de TGFVAR ou outra tabela
    query7 = f"""
    SELECT
        v.NUNOTA,
        v.CODPROD,
        v.NUMCOTACAO,
        v.SEQUENCIA
    FROM TGFVAR v
    WHERE v.NUNOTA = {NUNOTA_VENDA}
    """
    r7 = executar_query(access_token, query7, "TGFVAR (vinculos do pedido)")
    if r7 and r7.get("rows"):
        print(f"\nVinculos encontrados em TGFVAR:")
        for row in r7["rows"]:
            print(f"  NUNOTA: {row[0]}, CODPROD: {row[1]}, COTACAO: {row[2]}, SEQ: {row[3]}")
    else:
        print("\nNenhum vinculo em TGFVAR")

    # 8. VERIFICAR EMPENHO DO PEDIDO
    query8 = f"""
    SELECT
        e.NUNOTAPEDVEN,
        e.NUNOTA AS NUNOTA_COMPRA,
        e.CODPROD,
        e.QTDEMPENHO,
        cab.NUMNOTA,
        cab.CODPARC,
        par.NOMEPARC
    FROM TGWEMPE e
    LEFT JOIN TGFCAB cab ON cab.NUNOTA = e.NUNOTA
    LEFT JOIN TGFPAR par ON par.CODPARC = cab.CODPARC
    WHERE e.NUNOTAPEDVEN = {NUNOTA_VENDA}
    """
    r8 = executar_query(access_token, query8, "EMPENHOS DO PEDIDO (TGWEMPE)")
    if r8 and r8.get("rows"):
        print(f"\nEmpenhos encontrados: {len(r8['rows'])}")
        for row in r8["rows"]:
            print(f"  Produto {row[2]}: {row[3]} un - Compra {row[1]} (NF {row[4]}) - {row[6]}")
    else:
        print("\nNenhum empenho encontrado para este pedido!")

    # CONCLUSAO
    print("\n" + "=" * 70)
    print("ANALISE")
    print("=" * 70)
    print("""
O problema identificado:
- A query atual busca cotacao atraves do EMPENHO (compra_base)
- Se nao existe empenho, nao encontra a cotacao
- Precisamos encontrar COMO o Sankhya vincula a cotacao ao pedido de venda diretamente
    """)

if __name__ == "__main__":
    main()
