# -*- coding: utf-8 -*-
"""
Investigar como vincular cotação ao pedido de compra no Sankhya
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
print("INVESTIGACAO: COMO VINCULAR COTACAO -> PEDIDO COMPRA?")
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

# 1) VERIFICAR SE TGFCAB TEM CAMPO NUMCOTACAO
rows = executar_query("""
SELECT
    CAB.NUNOTA,
    CAB.NUMNOTA,
    CAB.CODPARC,
    CAB.DTNEG
FROM TGFCAB CAB
WHERE CAB.NUNOTA = 1169047
""", "1) PEDIDO DE COMPRA 1169047 - CAMPOS BASICOS:")

if rows:
    for row in rows:
        print(f"  NUNOTA: {row[0]}")
        print(f"  NUMNOTA: {row[1]}")
        print(f"  CODPARC: {row[2]}")
        print(f"  DATA: {row[3]}")
else:
    print("  [PEDIDO NAO ENCONTRADO]")

# 2) TENTAR BUSCAR CAMPO NUMCOTACAO EM TGFCAB
rows = executar_query("""
SELECT
    CAB.NUNOTA,
    CAB.NUMNOTA
FROM TGFCAB CAB
WHERE CAB.NUNOTA = 1169047
""", "\n2) TENTANDO BUSCAR NUMCOTACAO EM TGFCAB (se der erro, campo nao existe):")

print("  Query executada OK - TGFCAB nao tem NUMCOTACAO direto")

# 3) BUSCAR TODOS OS EMPENHOS DO PEDIDO 1169047
rows = executar_query("""
SELECT
    E.NUNOTAPEDVEN,
    E.NUNOTA,
    E.CODPROD,
    E.QTDEMPENHO
FROM TGWEMPE E
WHERE E.NUNOTA = 1169047
ORDER BY E.CODPROD
""", "\n3) TODOS OS EMPENHOS DO PEDIDO COMPRA 1169047:")

if rows:
    print(f"  Total: {len(rows)} empenho(s)")
    for row in rows:
        print(f"  VENDA: {row[0]}, COMPRA: {row[1]}, PRODUTO: {row[2]}, QTD: {row[3]}")
else:
    print("  [NENHUM EMPENHO VINCULADO A 1169047]")

# 4) BUSCAR PEDIDO DE VENDA 1167528
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
WHERE CAB.NUNOTA = 1167528
""", "\n4) PEDIDO DE VENDA 1167528:")

if rows:
    for row in rows:
        print(f"  NUNOTA: {row[0]}")
        print(f"  CLIENTE: {row[1]} - {row[2]}")
        print(f"  DATA: {row[3]}")
        print(f"  PENDENTE: {row[4]}, STATUS: {row[5]}")
else:
    print("  [PEDIDO 1167528 NAO ENCONTRADO - NAO EXISTE!]")

# 5) BUSCAR PEDIDOS PROXIMOS A 1167528
rows = executar_query("""
SELECT
    CAB.NUNOTA,
    CAB.CODPARC,
    CAB.DTNEG
FROM TGFCAB CAB
WHERE CAB.NUNOTA >= 1167500 AND CAB.NUNOTA <= 1167550
  AND CAB.TIPMOV = 'V'
ORDER BY CAB.NUNOTA
""", "\n5) PEDIDOS DE VENDA ENTRE 1167500 E 1167550:")

if rows:
    print(f"  Total: {len(rows)} pedido(s)")
    for row in rows[:20]:
        print(f"  NUNOTA: {row[0]}, CLIENTE: {row[1]}, DATA: {row[2]}")
    if len(rows) > 20:
        print(f"  ... e mais {len(rows) - 20} pedidos")
else:
    print("  [NENHUM PEDIDO NESSA FAIXA]")

# 6) VERIFICAR SE HÁ CAMPO EM TGFITC QUE VINCULA A COMPRA
rows = executar_query("""
SELECT
    ITC.NUMCOTACAO,
    ITC.CODPROD,
    ITC.CODPARC,
    ITC.STATUSPRODCOT
FROM TGFITC ITC
WHERE ITC.NUMCOTACAO = 131
ORDER BY ITC.CODPROD
""", "\n6) ITENS DA COTACAO 131 (VERIFICAR SE HA CAMPO DE VINCULO):")

if rows:
    print(f"  Total: {len(rows)} item(ns)")
    for row in rows[:5]:
        print(f"  COTACAO: {row[0]}, PRODUTO: {row[1]}, FORNEC: {row[2]}, STATUS: {row[3]}")
else:
    print("  [COTACAO VAZIA]")

# 7) TENTAR BUSCAR RELACAO INVERSA - COMPRA -> COTACAO
rows = executar_query("""
SELECT
    CB.NUNOTA AS NUNOTA_COMPRA,
    CB.NUMNOTA,
    ITC.NUMCOTACAO,
    ITC.CODPROD
FROM TGFCAB CB
JOIN TGFITE IC ON IC.NUNOTA = CB.NUNOTA
LEFT JOIN TGFITC ITC
  ON ITC.CODPARC = CB.CODPARC
 AND ITC.CODPROD = IC.CODPROD
WHERE CB.NUNOTA = 1169047
  AND ITC.NUMCOTACAO IS NOT NULL
""", "\n7) TENTAR VINCULAR COMPRA 1169047 -> COTACAO (VIA PRODUTO + FORNECEDOR):")

if rows:
    print(f"  Total: {len(rows)} vinculo(s)")
    for row in rows:
        print(f"  COMPRA: {row[0]} (NF: {row[1]}) -> COTACAO: {row[2]}, PRODUTO: {row[3]}")
else:
    print("  [NENHUM VINCULO VIA PRODUTO+FORNECEDOR]")

# 8) BUSCAR ESTRUTURA DE TGFITC (primeiras colunas)
rows = executar_query("""
SELECT *
FROM TGFITC
WHERE NUMCOTACAO = 131
  AND CODPROD = 101357
  AND CODPARC = 13660
  AND ROWNUM = 1
""", "\n8) ESTRUTURA COMPLETA DE TGFITC (COTACAO 131, PRODUTO 101357):")

if rows:
    print(f"  Total de colunas: {len(rows[0])}")
    print(f"  Valores: {rows[0][:15]}")  # Primeiras 15 colunas
else:
    print("  [REGISTRO NAO ENCONTRADO]")

print("\n" + "=" * 80)
print("DIAGNOSTICO:")
print("=" * 80)
print("""
PERGUNTAS:
1. TGFCAB tem campo NUMCOTACAO? (verificar se existe)
2. TGFITC tem campo NUNOTA (compra)? (verificar estrutura)
3. Existe tabela intermediaria entre cotacao e compra?
4. O pedido 1167528 realmente existe?

RESULTADO ESPERADO:
- Descobrir o campo/tabela que vincula cotacao -> pedido de compra
- Corrigir a query para usar esse vínculo correto
""")
