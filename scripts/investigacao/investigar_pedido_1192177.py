# -*- coding: utf-8 -*-
"""
Investigação do pedido 1192177 - Por que não aparece cotação?
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

NUNOTA = 1192177

print("=" * 80)
print(f"INVESTIGACAO DO PEDIDO {NUNOTA}")
print("=" * 80)

# 1. AUTENTICACAO
print("\n[1] Autenticando...")
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
    print(f"[ERRO] Autenticacao falhou: {auth_response.text}")
    exit(1)

access_token = auth_response.json()["access_token"]
print("[OK] Token obtido!")

# Query de investigação
query_investigacao = f"""
-- INVESTIGACAO PEDIDO {NUNOTA}

-- 1) VERIFICAR SE O PEDIDO EXISTE E SUAS PROPRIEDADES
SELECT
    'PEDIDO_CAB' AS ORIGEM,
    CAB.NUNOTA,
    CAB.CODTIPOPER,
    CAB.PENDENTE,
    CAB.STATUSNOTA,
    TOP.AD_RESERVAEMPENHO,
    NULL AS CODPROD,
    NULL AS QTDNEG,
    NULL AS QTDEMPENHO,
    NULL AS NUNOTA_COMPRA,
    NULL AS CODPARC_FORN,
    NULL AS NUMCOTACAO
FROM TGFCAB CAB
LEFT JOIN TGFTOP TOP ON TOP.CODTIPOPER = CAB.CODTIPOPER
WHERE CAB.NUNOTA = {NUNOTA}

UNION ALL

-- 2) VERIFICAR ITENS DO PEDIDO
SELECT
    'PEDIDO_ITE' AS ORIGEM,
    ITE.NUNOTA,
    NULL AS CODTIPOPER,
    NULL AS PENDENTE,
    NULL AS STATUSNOTA,
    NULL AS AD_RESERVAEMPENHO,
    ITE.CODPROD,
    ITE.QTDNEG,
    NULL AS QTDEMPENHO,
    NULL AS NUNOTA_COMPRA,
    NULL AS CODPARC_FORN,
    NULL AS NUMCOTACAO
FROM TGFITE ITE
WHERE ITE.NUNOTA = {NUNOTA}

UNION ALL

-- 3) VERIFICAR EMPENHO
SELECT
    'EMPENHO' AS ORIGEM,
    E.NUNOTAPEDVEN AS NUNOTA,
    NULL AS CODTIPOPER,
    NULL AS PENDENTE,
    NULL AS STATUSNOTA,
    NULL AS AD_RESERVAEMPENHO,
    E.CODPROD,
    NULL AS QTDNEG,
    E.QTDEMPENHO,
    E.NUNOTA AS NUNOTA_COMPRA,
    NULL AS CODPARC_FORN,
    NULL AS NUMCOTACAO
FROM TGWEMPE E
WHERE E.NUNOTAPEDVEN = {NUNOTA}

UNION ALL

-- 4) VERIFICAR COMPRAS VINCULADAS
SELECT
    'COMPRA_CAB' AS ORIGEM,
    E.NUNOTAPEDVEN AS NUNOTA,
    NULL AS CODTIPOPER,
    NULL AS PENDENTE,
    NULL AS STATUSNOTA,
    NULL AS AD_RESERVAEMPENHO,
    E.CODPROD,
    NULL AS QTDNEG,
    NULL AS QTDEMPENHO,
    CB.NUNOTA AS NUNOTA_COMPRA,
    CB.CODPARC AS CODPARC_FORN,
    NULL AS NUMCOTACAO
FROM TGWEMPE E
JOIN TGFCAB CB ON CB.NUNOTA = E.NUNOTA
WHERE E.NUNOTAPEDVEN = {NUNOTA}

UNION ALL

-- 5) VERIFICAR COTACAO DOS ITENS
SELECT
    'COTACAO_ITC' AS ORIGEM,
    E.NUNOTAPEDVEN AS NUNOTA,
    NULL AS CODTIPOPER,
    NULL AS PENDENTE,
    NULL AS STATUSNOTA,
    NULL AS AD_RESERVAEMPENHO,
    E.CODPROD,
    NULL AS QTDNEG,
    NULL AS QTDEMPENHO,
    CB.NUNOTA AS NUNOTA_COMPRA,
    CB.CODPARC AS CODPARC_FORN,
    ITC.NUMCOTACAO
FROM TGWEMPE E
JOIN TGFCAB CB ON CB.NUNOTA = E.NUNOTA
LEFT JOIN TGFITC ITC ON ITC.CODPARC = CB.CODPARC AND ITC.CODPROD = E.CODPROD
WHERE E.NUNOTAPEDVEN = {NUNOTA}
  AND ITC.NUMCOTACAO IS NOT NULL

ORDER BY ORIGEM, CODPROD
"""

print(f"\n[2] Executando query de investigacao para pedido {NUNOTA}...")

query_payload = {
    "requestBody": {
        "sql": query_investigacao.replace('\n', ' ').strip()
    }
}

query_response = requests.post(
    "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json=query_payload,
    timeout=120
)

print(f"Status: {query_response.status_code}")

if query_response.status_code != 200:
    print(f"[ERRO] Query falhou: {query_response.text}")
    exit(1)

result = query_response.json()

if result.get("status") != "1":
    print(f"[ERRO] Query retornou erro:")
    print(f"Status: {result.get('status')}")
    print(f"Mensagem: {result.get('statusMessage')}")
    exit(1)

print("[OK] Query executada com sucesso!")

# Processar resultado
response_body = result.get("responseBody", {})
fields = response_body.get("fieldsMetadata", [])
rows = response_body.get("rows", [])

print(f"\n[3] Resultado da investigacao:")
print("=" * 80)

if len(rows) == 0:
    print(f"\n[AVISO] Nenhum dado encontrado para o pedido {NUNOTA}!")
    print("\nPossiveis razoes:")
    print("  1. Pedido nao existe")
    print("  2. Pedido nao tem empenho")
    print("  3. Pedido nao atende aos criterios da query (PENDENTE='S', STATUSNOTA='L', AD_RESERVAEMPENHO='S')")
else:
    # Agrupar por origem
    pedido_cab = [r for r in rows if r[0] == 'PEDIDO_CAB']
    pedido_ite = [r for r in rows if r[0] == 'PEDIDO_ITE']
    empenho = [r for r in rows if r[0] == 'EMPENHO']
    compra_cab = [r for r in rows if r[0] == 'COMPRA_CAB']
    cotacao_itc = [r for r in rows if r[0] == 'COTACAO_ITC']

    print(f"\n1) PEDIDO CABECALHO ({len(pedido_cab)} registro(s)):")
    print("-" * 80)
    if pedido_cab:
        for row in pedido_cab:
            print(f"  NUNOTA: {row[1]}")
            print(f"  CODTIPOPER: {row[2]}")
            print(f"  PENDENTE: {row[3]}")
            print(f"  STATUSNOTA: {row[4]}")
            print(f"  AD_RESERVAEMPENHO: {row[5]}")
    else:
        print("  [NENHUM REGISTRO]")

    print(f"\n2) ITENS DO PEDIDO ({len(pedido_ite)} registro(s)):")
    print("-" * 80)
    if pedido_ite:
        for row in pedido_ite[:5]:
            print(f"  CODPROD: {row[6]}, QTDNEG: {row[7]}")
        if len(pedido_ite) > 5:
            print(f"  ... e mais {len(pedido_ite) - 5} itens")
    else:
        print("  [NENHUM REGISTRO]")

    print(f"\n3) EMPENHO ({len(empenho)} registro(s)):")
    print("-" * 80)
    if empenho:
        for row in empenho[:5]:
            print(f"  CODPROD: {row[6]}, QTDEMPENHO: {row[8]}, NUNOTA_COMPRA: {row[9]}")
        if len(empenho) > 5:
            print(f"  ... e mais {len(empenho) - 5} empenhos")
    else:
        print("  [NENHUM EMPENHO ENCONTRADO]")

    print(f"\n4) COMPRAS VINCULADAS ({len(compra_cab)} registro(s)):")
    print("-" * 80)
    if compra_cab:
        for row in compra_cab[:5]:
            print(f"  CODPROD: {row[6]}, NUNOTA_COMPRA: {row[9]}, FORNECEDOR: {row[10]}")
        if len(compra_cab) > 5:
            print(f"  ... e mais {len(compra_cab) - 5} compras")
    else:
        print("  [NENHUMA COMPRA VINCULADA]")

    print(f"\n5) COTACOES ENCONTRADAS ({len(cotacao_itc)} registro(s)):")
    print("-" * 80)
    if cotacao_itc:
        for row in cotacao_itc[:10]:
            print(f"  CODPROD: {row[6]}, FORNECEDOR: {row[10]}, NUMCOTACAO: {row[11]}")
        if len(cotacao_itc) > 10:
            print(f"  ... e mais {len(cotacao_itc) - 10} cotacoes")
    else:
        print("  [NENHUMA COTACAO ENCONTRADA]")
        print("\n  Possiveis razoes:")
        print("    - Fornecedor ainda nao cotou as pecas")
        print("    - JOIN entre TGFITC e compras nao esta correto")
        print("    - Cotacao foi feita mas nao esta vinculada ao fornecedor/produto")

print("\n" + "=" * 80)
print("DIAGNOSTICO CONCLUIDO!")
print("=" * 80)
