# -*- coding: utf-8 -*-
"""
Investigar empenho travado - pedido 1183490
Buscar alternativas para liberar
"""

import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), 'mcp_sankhya', '.env')
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
    if descricao:
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
    print("=" * 80)
    print("INVESTIGACAO EMPENHO TRAVADO - PEDIDO 1183490")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!")

    # 1. BUSCAR O PEDIDO 1183490 COM MAIS DETALHES
    query1 = """
    SELECT
        c.NUNOTA,
        c.NUMNOTA,
        c.CODEMP,
        c.CODPARC,
        c.DTNEG,
        c.VLRNOTA,
        c.PENDENTE,
        c.STATUSNOTA,
        c.STATUSNFE,
        c.TIPMOV,
        c.CODTIPOPER,
        c.DTFATUR,
        c.DTCANC,
        c.CONFIRESSION,
        c.DTALTER
    FROM TGFCAB c
    WHERE c.NUNOTA = 1183490
       OR c.NUMNOTA = 1183490
    """
    r1 = executar_query(access_token, query1, "Buscar pedido 1183490 (por NUNOTA ou NUMNOTA)")
    if r1 and r1.get("rows"):
        print("\nPedido encontrado:")
        fields = r1.get("fieldsMetadata", [])
        for i, field in enumerate(fields):
            print(f"  {field['name']}: {r1['rows'][0][i]}")
    else:
        print("\nPedido NAO encontrado diretamente")

    # 2. DETALHES DOS EMPENHOS DO 1183490
    query2 = """
    SELECT
        e.NUNOTAPEDVEN,
        e.NUNOTA AS NUNOTA_COMPRA,
        e.CODPROD,
        e.QTDEMPENHO,
        c.NUMNOTA AS NF_COMPRA,
        c.STATUSNOTA AS STATUS_COMPRA,
        c.PENDENTE AS PEND_COMPRA,
        c.DTFATUR AS FATUR_COMPRA
    FROM TGWEMPE e
    LEFT JOIN TGFCAB c ON c.NUNOTA = e.NUNOTA
    WHERE e.NUNOTAPEDVEN = 1183490
    """
    r2 = executar_query(access_token, query2, "Detalhes dos empenhos do 1183490")
    if r2 and r2.get("rows"):
        print(f"\n{len(r2['rows'])} empenhos encontrados:")
        print(f"\n{'COMPRA':>10} | {'CODPROD':>10} | {'QTDEMP':>8} | {'STATUS':>8} | {'PEND':>6} | FATURADO")
        print("-" * 70)
        for row in r2["rows"]:
            print(f"{row[1]:>10} | {row[2]:>10} | {row[3]:>8} | {str(row[5]):>8} | {str(row[6]):>6} | {str(row[7])[:10] if row[7] else 'NAO'}")

    # 3. VERIFICAR SE AS COMPRAS VINCULADAS FORAM RECEBIDAS
    query3 = """
    SELECT DISTINCT
        e.NUNOTA AS NUNOTA_COMPRA,
        c.NUMNOTA,
        c.STATUSNOTA,
        c.PENDENTE,
        c.DTFATUR,
        (SELECT COUNT(*) FROM TGWREC r WHERE r.NUNOTA = e.NUNOTA) AS TEM_RECEBIMENTO
    FROM TGWEMPE e
    JOIN TGFCAB c ON c.NUNOTA = e.NUNOTA
    WHERE e.NUNOTAPEDVEN = 1183490
    """
    r3 = executar_query(access_token, query3, "Status das compras vinculadas")
    if r3 and r3.get("rows"):
        print(f"\nCompras vinculadas aos empenhos:")
        print(f"\n{'NUNOTA':>10} | {'NUMNOTA':>10} | {'STATUS':>8} | {'PEND':>6} | {'FATURADO':<12} | RECEBIMENTO")
        print("-" * 75)
        for row in r3["rows"]:
            fatur = str(row[4])[:10] if row[4] else 'NAO'
            receb = 'SIM' if row[5] and row[5] > 0 else 'NAO'
            print(f"{row[0]:>10} | {row[1]:>10} | {str(row[2]):>8} | {str(row[3]):>6} | {fatur:<12} | {receb}")

    # 4. VERIFICAR ESTRUTURA DA TGWEMPE
    query4 = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGWEMPE'
    ORDER BY COLUMN_ID
    """
    r4 = executar_query(access_token, query4, "Estrutura da TGWEMPE")
    if r4 and r4.get("rows"):
        print("\nColunas da TGWEMPE:")
        for row in r4["rows"]:
            print(f"  - {row[0]} ({row[1]})")

    # 5. VERIFICAR SE EXISTE CAMPO DE STATUS/CANCELAMENTO NO EMPENHO
    query5 = """
    SELECT * FROM TGWEMPE WHERE NUNOTAPEDVEN = 1183490
    FETCH FIRST 1 ROWS ONLY
    """
    r5 = executar_query(access_token, query5, "Registro completo de um empenho")
    if r5 and r5.get("rows"):
        fields = r5.get("fieldsMetadata", [])
        print("\nCampos do empenho:")
        for i, field in enumerate(fields):
            print(f"  {field['name']}: {r5['rows'][0][i]}")

    # 6. ALTERNATIVA: Verificar se pode TRANSFERIR empenho
    print("\n" + "=" * 80)
    print("ALTERNATIVAS PARA RESOLVER")
    print("=" * 80)
    print("""
OPCAO 1: TRANSFERIR EMPENHO (via Sankhya)
-----------------------------------------
- Acessar: Central de Empenho
- Selecionar os empenhos do pedido 1183490
- Usar funcao "Transferir Empenho" para o pedido 1192177
- Isso mantem o vinculo com a compra mas muda o pedido de venda

OPCAO 2: CANCELAR A NOTA DE COMPRA E REFAZER
--------------------------------------------
- Se a compra ainda nao foi recebida fisicamente
- Cancelar a nota de compra
- Isso automaticamente cancela o empenho
- Depois, empenhar no pedido novo (1192177)

OPCAO 3: AJUSTE MANUAL NO BANCO (ULTIMO RECURSO)
------------------------------------------------
*** FAZER BACKUP ANTES! ***
*** TESTAR EM AMBIENTE DE HOMOLOGACAO PRIMEIRO! ***

-- 1. Ver os empenhos que serao alterados
SELECT * FROM TGWEMPE WHERE NUNOTAPEDVEN = 1183490;

-- 2. Transferir para o novo pedido
UPDATE TGWEMPE
SET NUNOTAPEDVEN = 1192177
WHERE NUNOTAPEDVEN = 1183490
  AND CODPROD IN (104319, 116860, 141544, 158802, 187790, 244788, 304061, 449061);

-- OU se preferir deletar (mais arriscado):
DELETE FROM TGWEMPE WHERE NUNOTAPEDVEN = 1183490;

OPCAO 4: VERIFICAR SE O PEDIDO 1183490 PODE SER "REABERTO"
----------------------------------------------------------
- Se o pedido foi cancelado mas nao deletado
- Tentar reabrir via tela de Pedidos
- Cancelar os empenhos
- Depois cancelar novamente o pedido
""")

    # 7. Verificar itens em comum entre 1183490 e 1192177
    query7 = """
    SELECT
        e1.CODPROD,
        e1.QTDEMPENHO AS EMP_ANTIGO,
        i2.QTDNEG AS QTDNEG_NOVO,
        NVL(e2.QTDEMPENHO, 0) AS EMP_NOVO,
        i2.QTDNEG - NVL(e2.QTDEMPENHO, 0) AS FALTA
    FROM TGWEMPE e1
    JOIN TGFITE i2 ON i2.CODPROD = e1.CODPROD AND i2.NUNOTA = 1192177
    LEFT JOIN (
        SELECT CODPROD, SUM(QTDEMPENHO) AS QTDEMPENHO
        FROM TGWEMPE WHERE NUNOTAPEDVEN = 1192177
        GROUP BY CODPROD
    ) e2 ON e2.CODPROD = e1.CODPROD
    WHERE e1.NUNOTAPEDVEN = 1183490
    """
    r7 = executar_query(access_token, query7, "Itens em comum que precisam transferir empenho")
    if r7 and r7.get("rows"):
        print(f"\nItens que precisam ter empenho transferido:")
        print(f"\n{'CODPROD':>10} | {'EMP_ANTIGO':>12} | {'QTDNEG_NOVO':>12} | {'EMP_NOVO':>10} | {'FALTA':>8}")
        print("-" * 65)
        for row in r7["rows"]:
            print(f"{row[0]:>10} | {row[1]:>12} | {row[2]:>12} | {row[3]:>10} | {row[4]:>8}")

if __name__ == "__main__":
    main()
