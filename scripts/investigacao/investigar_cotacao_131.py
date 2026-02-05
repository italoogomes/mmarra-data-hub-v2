# -*- coding: utf-8 -*-
"""
Investigar COTAÇÃO 131 - Qual pedido de compra está vinculado?
"""

import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

print("=" * 80)
print("INVESTIGACAO: COTACAO 131 - QUAL COMPRA ESTA VINCULADA?")
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

# 1) TODOS OS PRODUTOS DA COTAÇÃO 131
rows = executar_query("""
SELECT
    ITC.NUMCOTACAO,
    ITC.CODPROD,
    PRO.DESCRPROD,
    ITC.CODPARC,
    PAR.NOMEPARC,
    ITC.STATUSPRODCOT
FROM TGFITC ITC
LEFT JOIN TGFPRO PRO ON PRO.CODPROD = ITC.CODPROD
LEFT JOIN TGFPAR PAR ON PAR.CODPARC = ITC.CODPARC
WHERE ITC.NUMCOTACAO = 131
ORDER BY ITC.CODPROD, ITC.CODPARC
""", "1) TODOS OS PRODUTOS DA COTACAO 131:")

if rows:
    print(f"  Total: {len(rows)} item(ns)")
    for row in rows[:20]:
        print(f"  PRODUTO: {row[1]} - {str(row[2])[:40]}")
        print(f"    FORNECEDOR: {row[3]} - {str(row[4])[:40]}, STATUS: {row[5]}")
    if len(rows) > 20:
        print(f"  ... e mais {len(rows) - 20} itens")
else:
    print("  [COTACAO VAZIA]")

# 2) CABEÇALHO DA COTAÇÃO 131
rows = executar_query("""
SELECT
    COT.NUMCOTACAO,
    COT.CODUSURESP,
    USU.NOMEUSU,
    COT.SITUACAO,
    COT.DHINIC,
    COT.DHFINAL
FROM TGFCOT COT
LEFT JOIN TSIUSU USU ON USU.CODUSU = COT.CODUSURESP
WHERE COT.NUMCOTACAO = 131
""", "\n2) CABECALHO DA COTACAO 131:")

if rows:
    for row in rows:
        print(f"  NUMCOTACAO: {row[0]}")
        print(f"  RESPONSAVEL: {row[2]} (COD: {row[1]})")
        print(f"  SITUACAO: {row[3]}")
        print(f"  DHINIC: {row[4]}, DHFINAL: {row[5]}")
else:
    print("  [COTACAO NAO ENCONTRADA]")

# 3) BUSCAR TODOS OS PEDIDOS DE COMPRA COM PRODUTO 101357 E FORNECEDOR 13660
rows = executar_query("""
SELECT
    CAB.NUNOTA,
    CAB.NUMNOTA,
    CAB.DTNEG,
    ITE.CODPROD,
    ITE.QTDNEG,
    ITE.VLRUNIT,
    CAB.CODPARC
FROM TGFCAB CAB
JOIN TGFITE ITE ON ITE.NUNOTA = CAB.NUNOTA
WHERE CAB.TIPMOV = 'O'
  AND ITE.CODPROD = 101357
  AND CAB.CODPARC = 13660
  AND CAB.DTNEG >= TO_DATE('01/01/2026', 'DD/MM/YYYY')
ORDER BY CAB.DTNEG DESC
""", "\n3) PEDIDOS DE COMPRA COM PRODUTO 101357 E FORNECEDOR 13660 (2026):")

if rows:
    print(f"  Total: {len(rows)} pedido(s)")
    for row in rows:
        print(f"  NUNOTA: {row[0]}, NUMNOTA: {row[1]}, DATA: {row[2]}")
        print(f"    PRODUTO: {row[3]}, QTD: {row[4]}, VLR: {row[5]}")
        print()
else:
    print("  [NENHUM PEDIDO ENCONTRADO]")

# 4) EMPENHOS DESSES PEDIDOS DE COMPRA
rows = executar_query("""
SELECT
    E.NUNOTAPEDVEN,
    E.NUNOTA AS PEDIDO_COMPRA,
    E.CODPROD,
    E.QTDEMPENHO,
    CC.NUMNOTA AS NF_COMPRA,
    CV.CODPARC AS CLIENTE,
    CP.NOMEPARC AS NOME_CLIENTE
FROM TGWEMPE E
JOIN TGFCAB CC ON CC.NUNOTA = E.NUNOTA
LEFT JOIN TGFCAB CV ON CV.NUNOTA = E.NUNOTAPEDVEN
LEFT JOIN TGFPAR CP ON CP.CODPARC = CV.CODPARC
WHERE E.CODPROD = 101357
  AND CC.CODPARC = 13660
  AND CC.DTNEG >= TO_DATE('01/01/2026', 'DD/MM/YYYY')
ORDER BY E.NUNOTA DESC
""", "\n4) EMPENHOS DE COMPRAS DO PRODUTO 101357 (FORNECEDOR 13660, 2026):")

if rows:
    print(f"  Total: {len(rows)} empenho(s)")
    for row in rows:
        print(f"  VENDA: {row[0]} -> COMPRA: {row[1]} (NF: {row[4]})")
        print(f"    PRODUTO: {row[2]}, QTD: {row[3]}")
        print(f"    CLIENTE: {row[5]} - {str(row[6])[:40]}")
        print()
else:
    print("  [NENHUM EMPENHO ENCONTRADO]")

# 5) VERIFICAR SE COTAÇÃO ESTÁ VINCULADA A ALGUM PEDIDO DE COMPRA
# (Isso depende se há campo de vínculo direto - vamos ver)
rows = executar_query("""
SELECT
    ITC.NUMCOTACAO,
    ITC.CODPROD,
    ITC.CODPARC,
    CB.NUNOTA AS NUNOTA_COMPRA,
    CB.NUMNOTA,
    CB.DTNEG
FROM TGFITC ITC
LEFT JOIN TGFCAB CB
  ON CB.CODPARC = ITC.CODPARC
 AND CB.TIPMOV = 'O'
 AND CB.DTNEG >= TO_DATE('01/01/2026', 'DD/MM/YYYY')
LEFT JOIN TGFITE ITE
  ON ITE.NUNOTA = CB.NUNOTA
 AND ITE.CODPROD = ITC.CODPROD
WHERE ITC.NUMCOTACAO = 131
  AND ITC.CODPROD = 101357
  AND ITC.CODPARC = 13660
  AND CB.NUNOTA IS NOT NULL
ORDER BY CB.DTNEG DESC
""", "\n5) POSSIVEL VINCULO COTACAO 131 -> PEDIDO COMPRA (PRODUTO 101357):")

if rows:
    print(f"  Total: {len(rows)} vinculo(s) potencial(is)")
    for row in rows:
        print(f"  COTACAO: {row[0]}, PRODUTO: {row[1]}, FORNECEDOR: {row[2]}")
        print(f"  -> COMPRA: {row[3]} (NF: {row[4]}), DATA: {row[5]}")
        print()
else:
    print("  [NENHUM VINCULO DIRETO ENCONTRADO]")

# 6) BUSCAR PEDIDOS DE VENDA PRÓXIMOS A 1167528
rows = executar_query("""
SELECT
    CAB.NUNOTA,
    CAB.CODPARC,
    PAR.NOMEPARC,
    CAB.DTNEG,
    CAB.PENDENTE,
    CAB.STATUSNOTA
FROM TGFCAB CAB
LEFT JOIN TGFPAR PAR ON PAR.CODPARC = CAB.CODPARC
WHERE CAB.NUNOTA BETWEEN 1167520 AND 1167535
  AND CAB.TIPMOV = 'V'
ORDER BY CAB.NUNOTA
""", "\n6) PEDIDOS DE VENDA PROXIMOS A 1167528 (1167520-1167535):")

if rows:
    print(f"  Total: {len(rows)} pedido(s)")
    for row in rows:
        print(f"  NUNOTA: {row[0]}, CLIENTE: {row[1]} - {str(row[2])[:40]}")
        print(f"    DATA: {row[3]}, PEND: {row[4]}, STATUS: {row[5]}")
else:
    print("  [NENHUM PEDIDO NESSA FAIXA]")

print("\n" + "=" * 80)
print("DIAGNOSTICO:")
print("=" * 80)
print("""
DESCOBERTAS ESPERADAS:
1. Ver se há outros pedidos de compra além de 1168991 e 1169047
2. Ver se há empenho vinculando alguma venda ao pedido 1169047
3. Ver se pedido 1167528 está próximo numericamente mas não existe
4. Entender como cotação 131 se conecta aos pedidos de compra
""")
