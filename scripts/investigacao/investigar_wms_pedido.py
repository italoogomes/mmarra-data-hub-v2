# -*- coding: utf-8 -*-
"""
Investiga o status WMS detalhado de um pedido específico
"""

import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

PEDIDO = 1179409

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

    for row in rows:
        for i, val in enumerate(row):
            print(f"  {field_names[i]}: {val}")
        print("-" * 40)

# MAIN
print("=" * 80)
print(f"INVESTIGACAO WMS - PEDIDO {PEDIDO}")
print("=" * 80)

token = autenticar()
if not token:
    print("[ERRO] Falha na autenticacao")
    exit(1)
print("[OK] Autenticado!")

# 1. Buscar empenhos do pedido
print(f"\n\n[1] EMPENHOS DO PEDIDO {PEDIDO}...")
query_empenho = f"""
SELECT
    e.NUNOTAPEDVEN AS PEDIDO_VENDA,
    e.NUNOTA AS NUNOTA_COMPRA,
    e.CODPROD,
    e.QTDEMPENHO,
    cab.NUMNOTA,
    cab.TIPMOV,
    cab.DTNEG,
    cab.DTENTSAI,
    cab.PENDENTE,
    cab.CHAVENFE,
    par.NOMEPARC AS FORNECEDOR
FROM TGWEMPE e
JOIN TGFCAB cab ON cab.NUNOTA = e.NUNOTA
LEFT JOIN TGFPAR par ON par.CODPARC = cab.CODPARC
WHERE e.NUNOTAPEDVEN = {PEDIDO}
ORDER BY e.CODPROD
"""
result = executar_query(token, query_empenho, f"Empenhos do pedido {PEDIDO}")
imprimir_resultado(result)

# 2. Verificar status WMS das compras
print(f"\n\n[2] STATUS WMS DAS COMPRAS DO PEDIDO {PEDIDO}...")
query_wms = f"""
SELECT
    e.NUNOTAPEDVEN AS PEDIDO_VENDA,
    e.NUNOTA AS NUNOTA_COMPRA,
    cab.NUMNOTA,
    wms.SITUACAO,
    CASE wms.SITUACAO
        WHEN 0 THEN 'Pendente'
        WHEN 1 THEN 'Aguardando'
        WHEN 2 THEN 'Em Recebimento'
        WHEN 3 THEN 'Em Conferencia'
        WHEN 4 THEN 'Conferido'
        WHEN 5 THEN 'Em Armazenagem'
        WHEN 6 THEN 'Armazenado'
        ELSE 'Sem registro WMS'
    END AS STATUS_WMS,
    wms.DTRECEBIMENTO,
    wms.CONFFINAL
FROM TGWEMPE e
JOIN TGFCAB cab ON cab.NUNOTA = e.NUNOTA
LEFT JOIN TGWREC wms ON wms.NUNOTA = e.NUNOTA
WHERE e.NUNOTAPEDVEN = {PEDIDO}
"""
result = executar_query(token, query_wms, f"Status WMS das compras")
imprimir_resultado(result)

# 3. Verificar se existe na TGWREC
print(f"\n\n[3] VERIFICANDO TGWREC DIRETAMENTE...")
query_tgwrec = f"""
SELECT
    wms.*
FROM TGWREC wms
WHERE wms.NUNOTA IN (
    SELECT e.NUNOTA
    FROM TGWEMPE e
    WHERE e.NUNOTAPEDVEN = {PEDIDO}
)
"""
result = executar_query(token, query_tgwrec, "Registros TGWREC")
imprimir_resultado(result)

# 4. Verificar outras tabelas WMS que podem ter o status
print(f"\n\n[4] VERIFICANDO OUTRAS TABELAS WMS...")

# TGWSEP - Separação
query_sep = f"""
SELECT
    sep.NUNOTA,
    sep.SITUACAO,
    sep.CODPROD
FROM TGWSEP sep
WHERE sep.NUNOTA IN (
    SELECT e.NUNOTA
    FROM TGWEMPE e
    WHERE e.NUNOTAPEDVEN = {PEDIDO}
)
"""
result = executar_query(token, query_sep, "TGWSEP (Separação)")
imprimir_resultado(result)

# 5. Verificar colunas disponíveis em TGWREC
print(f"\n\n[5] COLUNAS DA TABELA TGWREC...")
query_cols = """
SELECT COLUMN_NAME, DATA_TYPE
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME = 'TGWREC'
ORDER BY COLUMN_NAME
"""
result = executar_query(token, query_cols, "Colunas TGWREC")
if result:
    fields = result.get("fieldsMetadata", [])
    rows = result.get("rows", [])
    print(f"\nTotal: {len(rows)} colunas")
    for row in rows[:30]:
        print(f"  {row[0]}: {row[1]}")

print("\n\n" + "=" * 80)
print("INVESTIGACAO CONCLUIDA!")
print("=" * 80)
