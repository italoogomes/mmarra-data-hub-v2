# -*- coding: utf-8 -*-
"""
Investigar divergência entre NUM_UNICO no CSV (1167205) vs tela (1167528)
Ambos ligados à cotação 131 e pedido compra 1169047
"""

import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

COTACAO = 131
PEDIDO_COMPRA = 1169047
CODPROD = 101357

print("=" * 80)
print("INVESTIGACAO: POR QUE PEDIDO 1167205 NO CSV VS 1167528 NA TELA?")
print("=" * 80)

# Autenticar
auth_response = requests.post(
    "https://api.sankhya.com.br/authenticate",
    headers={"Content-Type": "application/x-www-form-urlencoded", "X-Token": X_TOKEN},
    data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
    timeout=30
)
access_token = auth_response.json()["access_token"]
print("[OK] Autenticado!\n")

def executar_query(sql, titulo):
    print(f"\n{titulo}")
    print("-" * 80)

    query_payload = {"requestBody": {"sql": sql.replace('\n', ' ').strip()}}

    response = requests.post(
        "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json=query_payload,
        timeout=60
    )

    if response.status_code != 200:
        print(f"[ERRO] {response.text}")
        return []

    result = response.json()
    if result.get("status") != "1":
        print(f"[ERRO] {result.get('statusMessage')}")
        return []

    rows = result.get("responseBody", {}).get("rows", [])
    return rows

# 1) VERIFICAR COTAÇÃO 131
rows = executar_query(f"""
SELECT
    COT.NUMCOTACAO,
    ITC.CODPROD,
    ITC.CODPARC AS FORNECEDOR,
    ITC.STATUSPRODCOT,
    COT.CODUSURESP,
    USU.NOMEUSU
FROM TGFCOT COT
JOIN TGFITC ITC ON ITC.NUMCOTACAO = COT.NUMCOTACAO
LEFT JOIN TSIUSU USU ON USU.CODUSU = COT.CODUSURESP
WHERE COT.NUMCOTACAO = {COTACAO}
  AND ITC.CODPROD = {CODPROD}
""", "1) DADOS DA COTAÇÃO 131 (PRODUTO 101357):")

if rows:
    for row in rows:
        print(f"  COTACAO: {row[0]}")
        print(f"  PRODUTO: {row[1]}")
        print(f"  FORNECEDOR: {row[2]}")
        print(f"  STATUS: {row[3]}")
        print(f"  RESPONSAVEL: {row[5]}")
else:
    print("  [COTACAO NAO ENCONTRADA]")

# 2) VERIFICAR PEDIDO DE COMPRA 1169047
rows = executar_query(f"""
SELECT
    CAB.NUNOTA,
    CAB.NUMNOTA,
    CAB.CODPARC AS FORNECEDOR,
    PAR.NOMEPARC,
    CAB.DTNEG,
    CAB.TIPMOV
FROM TGFCAB CAB
LEFT JOIN TGFPAR PAR ON PAR.CODPARC = CAB.CODPARC
WHERE CAB.NUNOTA = {PEDIDO_COMPRA}
""", "\n2) PEDIDO DE COMPRA 1169047:")

if rows:
    for row in rows:
        print(f"  NUNOTA: {row[0]}")
        print(f"  NUMNOTA: {row[1]}")
        print(f"  FORNECEDOR: {row[2]} - {row[3]}")
        print(f"  DATA: {row[4]}")
        print(f"  TIPO: {row[5]}")
else:
    print("  [PEDIDO NAO ENCONTRADO]")

# 3) ITENS DO PEDIDO DE COMPRA 1169047
rows = executar_query(f"""
SELECT
    ITE.NUNOTA,
    ITE.CODPROD,
    PRO.DESCRPROD,
    ITE.QTDNEG,
    ITE.VLRUNIT
FROM TGFITE ITE
LEFT JOIN TGFPRO PRO ON PRO.CODPROD = ITE.CODPROD
WHERE ITE.NUNOTA = {PEDIDO_COMPRA}
  AND ITE.CODPROD = {CODPROD}
""", "\n3) ITENS DO PEDIDO COMPRA 1169047 (PRODUTO 101357):")

if rows:
    for row in rows:
        print(f"  NUNOTA: {row[0]}")
        print(f"  PRODUTO: {row[1]} - {row[2]}")
        print(f"  QTD: {row[3]}")
        print(f"  VLR UNIT: {row[4]}")
else:
    print("  [ITEM NAO ENCONTRADO]")

# 4) EMPENHOS VINCULADOS AO PEDIDO DE COMPRA 1169047
rows = executar_query(f"""
SELECT
    E.NUNOTAPEDVEN AS PEDIDO_VENDA,
    E.NUNOTA AS PEDIDO_COMPRA,
    E.CODPROD,
    E.QTDEMPENHO,
    CV.CODPARC AS CLIENTE,
    CP.NOMEPARC AS NOME_CLIENTE,
    CV.DTNEG AS DATA_VENDA
FROM TGWEMPE E
LEFT JOIN TGFCAB CV ON CV.NUNOTA = E.NUNOTAPEDVEN
LEFT JOIN TGFPAR CP ON CP.CODPARC = CV.CODPARC
WHERE E.NUNOTA = {PEDIDO_COMPRA}
  AND E.CODPROD = {CODPROD}
ORDER BY E.NUNOTAPEDVEN
""", "\n4) EMPENHOS LIGADOS AO PEDIDO COMPRA 1169047 (PRODUTO 101357):")

if rows:
    print(f"  Total: {len(rows)} empenho(s)")
    for row in rows:
        print(f"  -> VENDA: {row[0]}, COMPRA: {row[1]}, PRODUTO: {row[2]}")
        print(f"     QTD: {row[3]}, CLIENTE: {row[4]} - {row[5]}, DATA: {row[6]}")
        print()
else:
    print("  [NENHUM EMPENHO ENCONTRADO]")

# 5) VERIFICAR PEDIDOS DE VENDA 1167205 E 1167528
for pedido_venda in [1167205, 1167528]:
    rows = executar_query(f"""
    SELECT
        CAB.NUNOTA,
        CAB.CODPARC AS CLIENTE,
        PAR.NOMEPARC,
        CAB.DTNEG,
        CAB.DTPREVENT,
        CAB.PENDENTE,
        CAB.STATUSNOTA
    FROM TGFCAB CAB
    LEFT JOIN TGFPAR PAR ON PAR.CODPARC = CAB.CODPARC
    WHERE CAB.NUNOTA = {pedido_venda}
    """, f"\n5.{pedido_venda - 1167204}) PEDIDO DE VENDA {pedido_venda}:")

    if rows:
        for row in rows:
            print(f"  NUNOTA: {row[0]}")
            print(f"  CLIENTE: {row[1]} - {row[2]}")
            print(f"  DATA: {row[3]}")
            print(f"  PREVISAO: {row[4]}")
            print(f"  PENDENTE: {row[5]}, STATUS: {row[6]}")
    else:
        print(f"  [PEDIDO {pedido_venda} NAO ENCONTRADO]")

# 6) ITENS DOS PEDIDOS DE VENDA (PRODUTO 101357)
for pedido_venda in [1167205, 1167528]:
    rows = executar_query(f"""
    SELECT
        ITE.NUNOTA,
        ITE.CODPROD,
        ITE.QTDNEG
    FROM TGFITE ITE
    WHERE ITE.NUNOTA = {pedido_venda}
      AND ITE.CODPROD = {CODPROD}
    """, f"\n6.{pedido_venda - 1167204}) ITEM DO PEDIDO {pedido_venda} (PRODUTO 101357):")

    if rows:
        for row in rows:
            print(f"  NUNOTA: {row[0]}, PRODUTO: {row[1]}, QTD: {row[2]}")
    else:
        print(f"  [PRODUTO {CODPROD} NAO ENCONTRADO NO PEDIDO {pedido_venda}]")

# 7) VERIFICAR EMPENHOS DE AMBOS OS PEDIDOS
for pedido_venda in [1167205, 1167528]:
    rows = executar_query(f"""
    SELECT
        E.NUNOTAPEDVEN AS VENDA,
        E.NUNOTA AS COMPRA,
        E.CODPROD,
        E.QTDEMPENHO
    FROM TGWEMPE E
    WHERE E.NUNOTAPEDVEN = {pedido_venda}
      AND E.CODPROD = {CODPROD}
    """, f"\n7.{pedido_venda - 1167204}) EMPENHOS DO PEDIDO {pedido_venda} (PRODUTO 101357):")

    if rows:
        print(f"  Total: {len(rows)} empenho(s)")
        for row in rows:
            print(f"  VENDA: {row[0]}, COMPRA: {row[1]}, PRODUTO: {row[2]}, QTD: {row[3]}")
    else:
        print(f"  [PEDIDO {pedido_venda} NAO TEM EMPENHO PARA O PRODUTO {CODPROD}]")

# 8) ANALISAR QUERY - COMPRA_BASE
rows = executar_query(f"""
SELECT
    E.NUNOTAPEDVEN AS NUNOTA_VENDA,
    E.CODPROD,
    CB.NUNOTA AS NUNOTA_COMPRA,
    CB.CODPARC AS FORNECEDOR
FROM TGWEMPE E
JOIN TGFCAB CB ON CB.NUNOTA = E.NUNOTA
WHERE E.NUNOTA = {PEDIDO_COMPRA}
  AND E.CODPROD = {CODPROD}
""", "\n8) SIMULACAO DA CTE compra_base (PEDIDO COMPRA 1169047, PRODUTO 101357):")

if rows:
    print(f"  Total: {len(rows)} registro(s) na compra_base")
    for row in rows:
        print(f"  VENDA: {row[0]}, PRODUTO: {row[1]}, COMPRA: {row[2]}, FORNECEDOR: {row[3]}")
else:
    print("  [NENHUM REGISTRO NA compra_base]")

# 9) VERIFICAR SE HÁ MÚLTIPLOS EMPENHOS PARA MESMO PRODUTO/FORNECEDOR
rows = executar_query(f"""
SELECT
    E.NUNOTAPEDVEN,
    E.NUNOTA,
    E.CODPROD,
    CB.CODPARC,
    E.QTDEMPENHO,
    CV.DTNEG AS DATA_VENDA
FROM TGWEMPE E
JOIN TGFCAB CB ON CB.NUNOTA = E.NUNOTA
JOIN TGFCAB CV ON CV.NUNOTA = E.NUNOTAPEDVEN
WHERE E.CODPROD = {CODPROD}
  AND CB.CODPARC = 13660
  AND E.NUNOTA IN (1169047, {PEDIDO_COMPRA})
ORDER BY CV.DTNEG DESC
""", "\n9) TODOS OS EMPENHOS DO PRODUTO 101357 COM FORNECEDOR 13660:")

if rows:
    print(f"  Total: {len(rows)} empenho(s)")
    for row in rows:
        print(f"  VENDA: {row[0]}, COMPRA: {row[1]}, PRODUTO: {row[2]}, FORN: {row[3]}, QTD: {row[4]}, DATA: {row[5]}")
else:
    print("  [NENHUM EMPENHO ENCONTRADO]")

print("\n" + "=" * 80)
print("DIAGNOSTICO:")
print("=" * 80)
print("""
HIPOTESES:
1. Múltiplos empenhos do mesmo produto/fornecedor estão sendo agregados incorretamente
2. MAX() está pegando o pedido errado quando há múltiplos empenhos
3. JOIN entre compra_base e cotacao_info pode estar cruzando dados errados
4. Produto 101357 aparece em múltiplos pedidos de venda vinculados ao mesmo pedido de compra

ACAO NECESSARIA:
- Se houver múltiplos empenhos (VENDA1 + VENDA2 -> COMPRA1), nossa query pode estar
  pegando MAX(NUNOTAPEDVEN) errado ao consolidar por produto/fornecedor.
""")
