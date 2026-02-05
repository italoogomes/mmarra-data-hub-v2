# -*- coding: utf-8 -*-
"""
Investiga campos de XML/NFe na TGFCAB para compras vinculadas ao empenho
"""

import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

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

def imprimir_resultado(response_body):
    if not response_body:
        print("Sem resultado")
        return
    fields = response_body.get("fieldsMetadata", [])
    rows = response_body.get("rows", [])
    if not rows:
        print("Nenhum registro encontrado")
        return

    field_names = [f["name"] for f in fields]
    print(f"\nColunas: {field_names}")
    print(f"Total: {len(rows)} registros\n")

    for row in rows[:20]:
        for i, val in enumerate(row):
            print(f"  {field_names[i]}: {val}")
        print("-" * 40)

# MAIN
print("=" * 80)
print("INVESTIGACAO: CAMPOS XML/NFE NAS COMPRAS")
print("=" * 80)

token = autenticar()
if not token:
    print("[ERRO] Falha na autenticacao")
    exit(1)
print("[OK] Autenticado!")

# 1. Buscar colunas da TGFCAB relacionadas a NFe/XML
print("\n\n[1] BUSCANDO COLUNAS TGFCAB RELACIONADAS A NFE/XML...")
query_colunas = """
SELECT COLUMN_NAME, DATA_TYPE
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFCAB'
  AND (
    COLUMN_NAME LIKE '%NFE%'
    OR COLUMN_NAME LIKE '%XML%'
    OR COLUMN_NAME LIKE '%STATUS%'
    OR COLUMN_NAME LIKE '%ENTRADA%'
    OR COLUMN_NAME LIKE '%RECEB%'
    OR COLUMN_NAME LIKE '%CHAVE%'
  )
ORDER BY COLUMN_NAME
"""
result = executar_query(token, query_colunas, "Colunas NFe/XML na TGFCAB")
imprimir_resultado(result)

# 2. Verificar uma compra especifica (a do empenho do pedido 1191930)
print("\n\n[2] VERIFICANDO COMPRA 1193546 (empenho do pedido 1191930)...")
query_compra = """
SELECT
    cab.NUNOTA,
    cab.NUMNOTA,
    cab.TIPMOV,
    cab.STATUSNOTA,
    cab.STATUSNFE,
    cab.PENDENTE,
    cab.DTNEG,
    cab.DTENTSAI,
    cab.CHAVENFE
FROM TGFCAB cab
WHERE cab.NUNOTA = 1193546
"""
result = executar_query(token, query_compra, "Dados da compra 1193546")
imprimir_resultado(result)

# 3. Verificar status WMS dessa compra
print("\n\n[3] VERIFICANDO WMS DA COMPRA 1193546...")
query_wms = """
SELECT
    wms.NUNOTA,
    wms.SITUACAO,
    CASE wms.SITUACAO
        WHEN 0 THEN 'Pendente'
        WHEN 1 THEN 'Aguardando'
        WHEN 2 THEN 'Em Recebimento'
        WHEN 3 THEN 'Em Conferencia'
        WHEN 4 THEN 'Conferido'
        WHEN 5 THEN 'Em Armazenagem'
        WHEN 6 THEN 'Armazenado'
        ELSE 'Desconhecido'
    END AS STATUS_WMS,
    wms.DTRECEBIMENTO,
    wms.CONFFINAL
FROM TGWREC wms
WHERE wms.NUNOTA = 1193546
"""
result = executar_query(token, query_wms, "WMS da compra 1193546")
imprimir_resultado(result)

# 4. Verificar todas as compras de empenhos para entender padrao
print("\n\n[4] AMOSTRA: STATUS NFE/WMS DE COMPRAS VINCULADAS A EMPENHOS...")
query_amostra = """
SELECT * FROM (
    SELECT
        e.NUNOTAPEDVEN AS PEDIDO_VENDA,
        e.NUNOTA AS COMPRA_EMPENHO,
        cab.NUMNOTA,
        cab.TIPMOV,
        cab.STATUSNOTA,
        cab.STATUSNFE,
        cab.PENDENTE,
        cab.DTENTSAI,
        cab.CHAVENFE,
        wms.SITUACAO AS SIT_WMS,
        CASE wms.SITUACAO
            WHEN 0 THEN 'Pendente'
            WHEN 2 THEN 'Em Recebimento'
            WHEN 4 THEN 'Conferido'
            WHEN 6 THEN 'Armazenado'
            ELSE NVL(TO_CHAR(wms.SITUACAO), 'Sem WMS')
        END AS STATUS_WMS_DESC
    FROM TGWEMPE e
    JOIN TGFCAB cab ON cab.NUNOTA = e.NUNOTA
    LEFT JOIN TGWREC wms ON wms.NUNOTA = e.NUNOTA
    WHERE e.NUNOTAPEDVEN IN (1191930, 1167789, 1168009)
    ORDER BY e.NUNOTAPEDVEN
) WHERE ROWNUM <= 20
"""
result = executar_query(token, query_amostra, "Amostra de compras com empenho")
imprimir_resultado(result)

# 5. Verificar campos STATUSNFE - dominios possiveis
print("\n\n[5] VERIFICANDO DOMINIOS DE STATUSNFE...")
query_dominio = """
SELECT DISTINCT
    cab.STATUSNFE,
    COUNT(*) AS QTD
FROM TGFCAB cab
WHERE cab.TIPMOV = 'C'
GROUP BY cab.STATUSNFE
ORDER BY cab.STATUSNFE
"""
result = executar_query(token, query_dominio, "Valores distintos de STATUSNFE em compras")
imprimir_resultado(result)

print("\n\n" + "=" * 80)
print("INVESTIGACAO CONCLUIDA!")
print("=" * 80)
