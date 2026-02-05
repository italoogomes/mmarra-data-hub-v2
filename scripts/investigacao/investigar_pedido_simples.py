# -*- coding: utf-8 -*-
"""
Investigação simples do pedido 1192177
"""

import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

NUNOTA = 1192177

print("=" * 80)
print(f"INVESTIGACAO DO PEDIDO {NUNOTA}")
print("=" * 80)

# Autenticar
auth_response = requests.post(
    "https://api.sankhya.com.br/authenticate",
    headers={"Content-Type": "application/x-www-form-urlencoded", "X-Token": X_TOKEN},
    data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
    timeout=30
)
access_token = auth_response.json()["access_token"]
print("[OK] Autenticado!")

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

# 1) VERIFICAR PEDIDO
rows = executar_query(f"""
SELECT CAB.NUNOTA, CAB.CODTIPOPER, CAB.PENDENTE, CAB.STATUSNOTA, TOP.AD_RESERVAEMPENHO
FROM TGFCAB CAB
LEFT JOIN TGFTOP TOP ON TOP.CODTIPOPER = CAB.CODTIPOPER
WHERE CAB.NUNOTA = {NUNOTA}
""", "1) DADOS DO PEDIDO:")

if rows:
    for row in rows:
        print(f"  NUNOTA: {row[0]}")
        print(f"  CODTIPOPER: {row[1]}")
        print(f"  PENDENTE: {row[2]}")
        print(f"  STATUSNOTA: {row[3]}")
        print(f"  AD_RESERVAEMPENHO: {row[4]}")
else:
    print("  [PEDIDO NAO ENCONTRADO]")

# 2) ITENS DO PEDIDO
rows = executar_query(f"""
SELECT ITE.CODPROD, PRO.DESCRPROD, ITE.QTDNEG
FROM TGFITE ITE
LEFT JOIN TGFPRO PRO ON PRO.CODPROD = ITE.CODPROD
WHERE ITE.NUNOTA = {NUNOTA}
""", "\n2) ITENS DO PEDIDO:")

if rows:
    for row in rows[:10]:
        print(f"  CODPROD: {row[0]}, DESC: {str(row[1])[:30]}, QTD: {row[2]}")
    if len(rows) > 10:
        print(f"  ... e mais {len(rows) - 10} itens")
else:
    print("  [SEM ITENS]")

# 3) EMPENHO
rows = executar_query(f"""
SELECT E.CODPROD, E.QTDEMPENHO, E.NUNOTA AS NUNOTA_COMPRA
FROM TGWEMPE E
WHERE E.NUNOTAPEDVEN = {NUNOTA}
""", "\n3) EMPENHO:")

if rows:
    print(f"  Total: {len(rows)} empenhos")
    for row in rows[:10]:
        print(f"  CODPROD: {row[0]}, QTDEMPENHO: {row[1]}, NUNOTA_COMPRA: {row[2]}")
    if len(rows) > 10:
        print(f"  ... e mais {len(rows) - 10} empenhos")
else:
    print("  [SEM EMPENHO]")

# 4) COMPRAS VINCULADAS
rows = executar_query(f"""
SELECT E.CODPROD, CB.NUNOTA AS NUNOTA_COMPRA, CB.CODPARC AS FORNECEDOR
FROM TGWEMPE E
JOIN TGFCAB CB ON CB.NUNOTA = E.NUNOTA
WHERE E.NUNOTAPEDVEN = {NUNOTA}
""", "\n4) COMPRAS VINCULADAS:")

if rows:
    print(f"  Total: {len(rows)} compras")
    for row in rows[:10]:
        print(f"  CODPROD: {row[0]}, NUNOTA_COMPRA: {row[1]}, FORNECEDOR: {row[2]}")
    if len(rows) > 10:
        print(f"  ... e mais {len(rows) - 10} compras")
else:
    print("  [SEM COMPRAS VINCULADAS]")

# 5) COTACOES (TGFITC)
rows = executar_query(f"""
SELECT E.CODPROD, CB.CODPARC AS FORNECEDOR, ITC.NUMCOTACAO, ITC.STATUSPRODCOT
FROM TGWEMPE E
JOIN TGFCAB CB ON CB.NUNOTA = E.NUNOTA
LEFT JOIN TGFITC ITC ON ITC.CODPARC = CB.CODPARC AND ITC.CODPROD = E.CODPROD
WHERE E.NUNOTAPEDVEN = {NUNOTA}
  AND ITC.NUMCOTACAO IS NOT NULL
""", "\n5) COTACOES (TGFITC):")

if rows:
    print(f"  Total: {len(rows)} cotacoes encontradas")
    for row in rows[:10]:
        print(f"  CODPROD: {row[0]}, FORNECEDOR: {row[1]}, NUMCOTACAO: {row[2]}, STATUS: {row[3]}")
    if len(rows) > 10:
        print(f"  ... e mais {len(rows) - 10} cotacoes")
else:
    print("  [NENHUMA COTACAO ENCONTRADA EM TGFITC]")
    print("  Isso significa que o JOIN entre compras e TGFITC nao esta retornando nada.")

# 6) CABECALHO COTACAO (TGFCOT)
rows = executar_query(f"""
SELECT COT.NUMCOTACAO, COT.SITUACAO, COT.CODUSURESP, USU.NOMEUSU
FROM TGWEMPE E
JOIN TGFCAB CB ON CB.NUNOTA = E.NUNOTA
LEFT JOIN TGFITC ITC ON ITC.CODPARC = CB.CODPARC AND ITC.CODPROD = E.CODPROD
LEFT JOIN TGFCOT COT ON COT.NUMCOTACAO = ITC.NUMCOTACAO
LEFT JOIN TSIUSU USU ON USU.CODUSU = COT.CODUSURESP
WHERE E.NUNOTAPEDVEN = {NUNOTA}
  AND COT.NUMCOTACAO IS NOT NULL
""", "\n6) CABECALHO COTACAO (TGFCOT):")

if rows:
    print(f"  Total: {len(rows)} cotacoes com cabecalho")
    for row in rows[:10]:
        print(f"  NUMCOTACAO: {row[0]}, SITUACAO: {row[1]}, RESPONSAVEL: {row[3]}")
    if len(rows) > 10:
        print(f"  ... e mais {len(rows) - 10} cotacoes")
else:
    print("  [NENHUM CABECALHO DE COTACAO ENCONTRADO]")

print("\n" + "=" * 80)
print("DIAGNOSTICO CONCLUIDO!")
print("=" * 80)
