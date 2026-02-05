# -*- coding: utf-8 -*-
"""
Investiga um pedido especifico para verificar status de faturamento
"""

import os
import requests
from dotenv import load_dotenv

# Subir 2 níveis (scripts/investigacao -> raiz) e entrar em mcp_sankhya
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

NUNOTA = 1191930  # Pedido a investigar

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
    print(f"INVESTIGACAO DO PEDIDO {NUNOTA}")
    print("=" * 70)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!")

    # 1. DADOS DO CABECALHO (TGFCAB)
    query1 = f"""
    SELECT
        c.NUNOTA,
        c.NUMNOTA,
        c.CODEMP,
        c.CODPARC,
        p.NOMEPARC AS CLIENTE,
        c.DTNEG,
        c.VLRNOTA,
        c.PENDENTE,
        c.STATUSNOTA,
        c.STATUSNFE,
        c.TIPMOV,
        c.CODTIPOPER,
        t.DESCROPER AS TIPO_OPERACAO,
        c.CODVEND,
        v.APELIDO AS VENDEDOR,
        c.DTFATUR,
        c.DTPREVENT,
        c.OBSERVACAO
    FROM TGFCAB c
    LEFT JOIN TGFPAR p ON p.CODPARC = c.CODPARC
    LEFT JOIN TGFVEN v ON v.CODVEND = c.CODVEND
    LEFT JOIN (
        SELECT CODTIPOPER, DESCROPER,
               ROW_NUMBER() OVER (PARTITION BY CODTIPOPER ORDER BY DHALTER DESC) AS RN
        FROM TGFTOP
    ) t ON t.CODTIPOPER = c.CODTIPOPER AND t.RN = 1
    WHERE c.NUNOTA = {NUNOTA}
    """
    r1 = executar_query(access_token, query1, "DADOS DO CABECALHO (TGFCAB)")
    if r1 and r1.get("rows"):
        row = r1["rows"][0]
        fields = r1.get("fieldsMetadata", [])

        print("\n" + "-"*50)
        print("INFORMACOES GERAIS DO PEDIDO")
        print("-"*50)
        for i, field in enumerate(fields):
            valor = row[i] if i < len(row) else None
            print(f"  {field['name']:<15}: {valor}")

        # Interpretar status
        pendente = row[7]  # PENDENTE
        statusnota = row[8]  # STATUSNOTA
        statusnfe = row[9]  # STATUSNFE
        dtfatur = row[15]  # DTFATUR

        print("\n" + "-"*50)
        print("ANALISE DE STATUS")
        print("-"*50)

        # PENDENTE
        if pendente == 'S':
            print("  PENDENTE = 'S' --> Pedido AINDA NAO FATURADO (em aberto)")
        elif pendente == 'N':
            print("  PENDENTE = 'N' --> Pedido JA PROCESSADO/FATURADO")
        else:
            print(f"  PENDENTE = '{pendente}' --> Status desconhecido")

        # STATUSNOTA
        status_desc = {
            'L': 'Liberado',
            'P': 'Pendente de aprovacao',
            'A': 'Aguardando',
            'C': 'Cancelado',
            'F': 'Faturado'
        }
        desc = status_desc.get(statusnota, 'Desconhecido')
        print(f"  STATUSNOTA = '{statusnota}' --> {desc}")

        # STATUSNFE
        if statusnfe:
            nfe_desc = {
                'A': 'Autorizada',
                'D': 'Denegada',
                'R': 'Rejeitada',
                'P': 'Pendente',
                'C': 'Cancelada'
            }
            desc_nfe = nfe_desc.get(statusnfe, 'Desconhecido')
            print(f"  STATUSNFE = '{statusnfe}' --> {desc_nfe}")

        # DTFATUR
        if dtfatur:
            print(f"  DTFATUR = {dtfatur} --> JA FOI FATURADO!")
        else:
            print(f"  DTFATUR = NULL --> AINDA NAO FATURADO")

    # 2. ITENS DO PEDIDO
    query2 = f"""
    SELECT
        i.SEQUENCIA,
        i.CODPROD,
        p.DESCRPROD,
        i.QTDNEG,
        i.VLRUNIT,
        i.VLRTOT,
        i.PENDENTE AS ITEM_PENDENTE,
        i.STATUSNOTA AS ITEM_STATUS
    FROM TGFITE i
    LEFT JOIN TGFPRO p ON p.CODPROD = i.CODPROD
    WHERE i.NUNOTA = {NUNOTA}
    ORDER BY i.SEQUENCIA
    """
    r2 = executar_query(access_token, query2, "ITENS DO PEDIDO")
    if r2 and r2.get("rows"):
        print(f"\nTotal de itens: {len(r2['rows'])}")
        print(f"\n{'SEQ':>4} | {'CODPROD':>8} | {'QTDNEG':>8} | {'VLRTOT':>12} | {'PEND':>4} | {'STAT':>4} | PRODUTO")
        print("-" * 80)
        for row in r2["rows"][:15]:
            print(f"{row[0]:>4} | {row[1]:>8} | {row[3]:>8} | {str(row[5]):>12} | {str(row[6]):>4} | {str(row[7]):>4} | {str(row[2])[:25]}")
        if len(r2["rows"]) > 15:
            print(f"... e mais {len(r2['rows']) - 15} itens")

    # 3. VERIFICAR EMPENHO
    query3 = f"""
    SELECT
        e.NUNOTAPEDVEN,
        e.NUNOTA AS NUNOTA_COMPRA,
        e.CODPROD,
        e.QTDEMPENHO,
        c.NUMNOTA AS NF_COMPRA,
        c.CODPARC AS FORNECEDOR
    FROM TGWEMPE e
    LEFT JOIN TGFCAB c ON c.NUNOTA = e.NUNOTA
    WHERE e.NUNOTAPEDVEN = {NUNOTA}
    """
    r3 = executar_query(access_token, query3, "EMPENHOS DO PEDIDO")
    if r3 and r3.get("rows"):
        print(f"\nEmpenhos encontrados: {len(r3['rows'])}")
        for row in r3["rows"][:10]:
            print(f"  Produto {row[2]}: {row[3]} un empenhadas (Compra: {row[1]})")
    else:
        print("\nNenhum empenho encontrado para este pedido")

    # 4. VERIFICAR WMS
    query4 = f"""
    SELECT * FROM VGWSEPSITCAB WHERE NUNOTA = {NUNOTA}
    """
    r4 = executar_query(access_token, query4, "STATUS WMS (VGWSEPSITCAB)")
    if r4 and r4.get("rows"):
        print("\nPedido ESTA no WMS")
        fields = r4.get("fieldsMetadata", [])
        for i, field in enumerate(fields[:10]):
            print(f"  {field['name']}: {r4['rows'][0][i]}")
    else:
        print("\nPedido NAO ESTA no WMS (ou nao encontrado)")

    # 5. VERIFICAR FINANCEIRO
    query5 = f"""
    SELECT
        f.NUFIN,
        f.DTVENC,
        f.VLRDESDOB,
        f.DHBAIXA,
        CASE f.RECDESP WHEN 1 THEN 'RECEBER' ELSE 'PAGAR' END AS TIPO
    FROM TGFFIN f
    WHERE f.NUNOTA = {NUNOTA}
    """
    r5 = executar_query(access_token, query5, "TITULOS FINANCEIROS")
    if r5 and r5.get("rows"):
        print(f"\nTitulos encontrados: {len(r5['rows'])}")
        for row in r5["rows"]:
            baixa = "BAIXADO" if row[3] else "EM ABERTO"
            print(f"  {row[4]} - Venc: {str(row[1])[:10]} - R$ {row[2]} - {baixa}")
    else:
        print("\nNenhum titulo financeiro vinculado")

    # 6. VERIFICAR BLOQUEIOS
    query6 = f"""
    SELECT
        b.NUNOTA,
        b.SEQUENCIA,
        b.CODBLOQ,
        b.DHBLOQUEIO,
        b.DHDESBLOQUEIO,
        b.OBSERVACAO
    FROM TGFBLQ b
    WHERE b.NUNOTA = {NUNOTA}
    """
    r6 = executar_query(access_token, query6, "BLOQUEIOS DO PEDIDO")
    if r6 and r6.get("rows"):
        print(f"\nBloqueios encontrados: {len(r6['rows'])}")
        for row in r6["rows"]:
            desbloq = row[4] if row[4] else "AINDA BLOQUEADO"
            print(f"  Bloqueio {row[2]} em {str(row[3])[:10]} - Desbloqueio: {desbloq}")
            if row[5]:
                print(f"    Obs: {row[5][:50]}")
    else:
        print("\nNenhum bloqueio encontrado")

    # CONCLUSAO
    print("\n" + "=" * 70)
    print("CONCLUSAO")
    print("=" * 70)

    if r1 and r1.get("rows"):
        row = r1["rows"][0]
        pendente = row[7]
        statusnota = row[8]
        dtfatur = row[15]

        if dtfatur:
            print("\n>>> PEDIDO JA FOI FATURADO! <<<")
        elif pendente == 'S' and statusnota == 'L':
            print("\n>>> PEDIDO LIBERADO PARA FATURAR <<<")
            print("    (PENDENTE='S' e STATUSNOTA='L')")
        elif pendente == 'S' and statusnota == 'P':
            print("\n>>> PEDIDO PENDENTE DE APROVACAO <<<")
            print("    (PENDENTE='S' e STATUSNOTA='P')")
        elif pendente == 'N':
            print("\n>>> PEDIDO JA PROCESSADO <<<")
        else:
            print(f"\n>>> STATUS: PENDENTE='{pendente}', STATUSNOTA='{statusnota}' <<<")

if __name__ == "__main__":
    main()
