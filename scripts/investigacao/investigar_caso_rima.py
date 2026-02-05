# -*- coding: utf-8 -*-
"""
CASO RIMA - Investigacao completa
Pedido original: 1183490 (cancelado)
Pedido duplicado: 1192177 (parcial, aguardando)
Pedido derivado: 1192208 (item 446518)
"""

import os
import requests
from dotenv import load_dotenv

# Caminho do .env na raiz do projeto
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(project_root, 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

PEDIDOS = [1183490, 1192177, 1192208]
ITEM_VERIFICAR = 446518

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

def executar_query(access_token, query_sql):
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
            return None
        return result.get("responseBody", {})
    except:
        return None

def main():
    print("=" * 80)
    print("CASO RIMA - INVESTIGACAO COMPLETA")
    print("=" * 80)
    print(f"Pedidos: {PEDIDOS}")
    print(f"Item a verificar: {ITEM_VERIFICAR}")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!\n")

    # ========================================
    # 1. STATUS DOS 3 PEDIDOS
    # ========================================
    print("\n" + "=" * 80)
    print("1. STATUS DOS PEDIDOS")
    print("=" * 80)

    for nunota in PEDIDOS:
        query = f"""
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
            c.TIPMOV,
            c.CODTIPOPER,
            c.DTFATUR,
            (SELECT COUNT(*) FROM TGFITE i WHERE i.NUNOTA = c.NUNOTA) AS QTD_ITENS
        FROM TGFCAB c
        LEFT JOIN TGFPAR p ON p.CODPARC = c.CODPARC
        WHERE c.NUNOTA = {nunota}
        """
        r = executar_query(access_token, query)
        if r and r.get("rows"):
            row = r["rows"][0]
            print(f"\n--- PEDIDO {nunota} ---")
            print(f"  NUMNOTA: {row[1]}")
            print(f"  EMPRESA: {row[2]}")
            print(f"  CLIENTE: {row[4]}")
            print(f"  DATA: {str(row[5])[:10]}")
            print(f"  VALOR: R$ {row[6]:,.2f}" if row[6] else "  VALOR: -")
            print(f"  PENDENTE: {row[7]}")
            print(f"  STATUSNOTA: {row[8]}")
            print(f"  TIPMOV: {row[9]}")
            print(f"  DTFATUR: {row[11]}")
            print(f"  QTD_ITENS: {row[12]}")

            # Interpretar status
            if row[8] == 'C':
                print(f"  >>> STATUS: CANCELADO <<<")
            elif row[11]:
                print(f"  >>> STATUS: FATURADO <<<")
            elif row[7] == 'S' and row[8] == 'L':
                print(f"  >>> STATUS: LIBERADO (aguardando faturamento) <<<")
            elif row[7] == 'S' and row[8] == 'P':
                print(f"  >>> STATUS: PENDENTE APROVACAO <<<")
        else:
            print(f"\n--- PEDIDO {nunota} ---")
            print(f"  NAO ENCONTRADO!")

    # ========================================
    # 2. ITEM 446518 NOS PEDIDOS
    # ========================================
    print("\n" + "=" * 80)
    print(f"2. ITEM {ITEM_VERIFICAR} NOS PEDIDOS")
    print("=" * 80)

    for nunota in PEDIDOS:
        query = f"""
        SELECT
            i.NUNOTA,
            i.CODPROD,
            p.DESCRPROD,
            i.QTDNEG,
            i.VLRUNIT,
            i.VLRTOT,
            i.PENDENTE,
            i.STATUSNOTA
        FROM TGFITE i
        LEFT JOIN TGFPRO p ON p.CODPROD = i.CODPROD
        WHERE i.NUNOTA = {nunota} AND i.CODPROD = {ITEM_VERIFICAR}
        """
        r = executar_query(access_token, query)
        if r and r.get("rows"):
            row = r["rows"][0]
            print(f"\n  Pedido {nunota}: SIM - Qtd: {row[3]}, Valor: R$ {row[5]}")
            print(f"    Produto: {row[2]}")
            print(f"    Pendente: {row[6]}, Status: {row[7]}")
        else:
            print(f"\n  Pedido {nunota}: NAO CONTEM item {ITEM_VERIFICAR}")

    # ========================================
    # 3. EMPENHOS DO PEDIDO CANCELADO (1183490)
    # ========================================
    print("\n" + "=" * 80)
    print("3. EMPENHOS DO PEDIDO CANCELADO (1183490)")
    print("=" * 80)

    query = f"""
    SELECT
        e.NUNOTAPEDVEN,
        e.NUNOTA AS NUNOTA_COMPRA,
        e.CODPROD,
        p.DESCRPROD,
        e.QTDEMPENHO
    FROM TGWEMPE e
    LEFT JOIN TGFPRO p ON p.CODPROD = e.CODPROD
    WHERE e.NUNOTAPEDVEN = 1183490
    ORDER BY e.CODPROD
    """
    r = executar_query(access_token, query)
    if r and r.get("rows"):
        print(f"\n  ATENCAO: {len(r['rows'])} empenhos AINDA VINCULADOS ao pedido cancelado!")
        print(f"\n  {'CODPROD':>10} | {'QTDEMP':>8} | {'COMPRA':>10} | PRODUTO")
        print("  " + "-" * 70)
        for row in r["rows"][:20]:
            print(f"  {row[2]:>10} | {row[4]:>8} | {row[1]:>10} | {str(row[3])[:35]}")
        if len(r["rows"]) > 20:
            print(f"  ... e mais {len(r['rows']) - 20} itens")

        # Verificar se item 446518 esta empenhado no pedido cancelado
        for row in r["rows"]:
            if row[2] == ITEM_VERIFICAR:
                print(f"\n  !!! ITEM {ITEM_VERIFICAR} ESTA EMPENHADO NO PEDIDO CANCELADO !!!")
                print(f"      Qtd empenhada: {row[4]}")
                print(f"      Compra vinculada: {row[1]}")
    else:
        print("\n  Nenhum empenho encontrado para o pedido 1183490")

    # ========================================
    # 4. EMPENHOS DO PEDIDO 1192177
    # ========================================
    print("\n" + "=" * 80)
    print("4. EMPENHOS DO PEDIDO 1192177")
    print("=" * 80)

    query = f"""
    SELECT
        e.NUNOTAPEDVEN,
        e.NUNOTA AS NUNOTA_COMPRA,
        e.CODPROD,
        p.DESCRPROD,
        e.QTDEMPENHO
    FROM TGWEMPE e
    LEFT JOIN TGFPRO p ON p.CODPROD = e.CODPROD
    WHERE e.NUNOTAPEDVEN = 1192177
    ORDER BY e.CODPROD
    """
    r = executar_query(access_token, query)
    if r and r.get("rows"):
        print(f"\n  {len(r['rows'])} empenhos no pedido 1192177")
        print(f"\n  {'CODPROD':>10} | {'QTDEMP':>8} | {'COMPRA':>10} | PRODUTO")
        print("  " + "-" * 70)
        for row in r["rows"][:15]:
            print(f"  {row[2]:>10} | {row[4]:>8} | {row[1]:>10} | {str(row[3])[:35]}")
    else:
        print("\n  Nenhum empenho no pedido 1192177")

    # ========================================
    # 5. ITENS SEM EMPENHO NO 1192177
    # ========================================
    print("\n" + "=" * 80)
    print("5. ITENS SEM EMPENHO NO PEDIDO 1192177")
    print("=" * 80)

    query = f"""
    SELECT
        i.CODPROD,
        p.DESCRPROD,
        i.QTDNEG,
        NVL(e.QTDEMPENHO, 0) AS QTDEMP,
        i.QTDNEG - NVL(e.QTDEMPENHO, 0) AS FALTA_EMPENHO
    FROM TGFITE i
    LEFT JOIN TGFPRO p ON p.CODPROD = i.CODPROD
    LEFT JOIN (
        SELECT NUNOTAPEDVEN, CODPROD, SUM(QTDEMPENHO) AS QTDEMPENHO
        FROM TGWEMPE
        WHERE NUNOTAPEDVEN = 1192177
        GROUP BY NUNOTAPEDVEN, CODPROD
    ) e ON e.CODPROD = i.CODPROD
    WHERE i.NUNOTA = 1192177
      AND (e.QTDEMPENHO IS NULL OR e.QTDEMPENHO < i.QTDNEG)
    ORDER BY i.CODPROD
    """
    r = executar_query(access_token, query)
    if r and r.get("rows"):
        print(f"\n  {len(r['rows'])} itens SEM empenho completo:")
        print(f"\n  {'CODPROD':>10} | {'QTDNEG':>8} | {'QTDEMP':>8} | {'FALTA':>8} | PRODUTO")
        print("  " + "-" * 75)
        for row in r["rows"]:
            print(f"  {row[0]:>10} | {row[2]:>8} | {row[3]:>8} | {row[4]:>8} | {str(row[1])[:30]}")
    else:
        print("\n  Todos os itens estao empenhados!")

    # ========================================
    # 6. VERIFICAR EMPENHO DUPLICADO
    # ========================================
    print("\n" + "=" * 80)
    print("6. ITENS EMPENHADOS EM AMBOS PEDIDOS (1183490 e 1192177)")
    print("=" * 80)

    query = f"""
    SELECT
        e1.CODPROD,
        p.DESCRPROD,
        e1.QTDEMPENHO AS EMP_1183490,
        e2.QTDEMPENHO AS EMP_1192177,
        e1.NUNOTA AS COMPRA_1183490,
        e2.NUNOTA AS COMPRA_1192177
    FROM TGWEMPE e1
    JOIN TGWEMPE e2 ON e2.CODPROD = e1.CODPROD AND e2.NUNOTAPEDVEN = 1192177
    LEFT JOIN TGFPRO p ON p.CODPROD = e1.CODPROD
    WHERE e1.NUNOTAPEDVEN = 1183490
    ORDER BY e1.CODPROD
    """
    r = executar_query(access_token, query)
    if r and r.get("rows"):
        print(f"\n  !!! {len(r['rows'])} itens com EMPENHO DUPLICADO !!!")
        print(f"\n  {'CODPROD':>10} | {'EMP_CANC':>10} | {'EMP_NOVO':>10} | PRODUTO")
        print("  " + "-" * 70)
        for row in r["rows"]:
            print(f"  {row[0]:>10} | {row[2]:>10} | {row[3]:>10} | {str(row[1])[:35]}")
    else:
        print("\n  Nenhum item com empenho duplicado")

    # ========================================
    # 7. PEDIDO 1192208 - VERIFICAR ITEM 446518
    # ========================================
    print("\n" + "=" * 80)
    print("7. PEDIDO 1192208 - TODOS OS ITENS")
    print("=" * 80)

    query = f"""
    SELECT
        i.CODPROD,
        p.DESCRPROD,
        i.QTDNEG,
        i.VLRTOT,
        i.PENDENTE,
        i.STATUSNOTA
    FROM TGFITE i
    LEFT JOIN TGFPRO p ON p.CODPROD = i.CODPROD
    WHERE i.NUNOTA = 1192208
    ORDER BY i.CODPROD
    """
    r = executar_query(access_token, query)
    if r and r.get("rows"):
        print(f"\n  {len(r['rows'])} itens no pedido 1192208:")
        print(f"\n  {'CODPROD':>10} | {'QTDNEG':>8} | {'VLRTOT':>12} | PRODUTO")
        print("  " + "-" * 70)
        tem_446518 = False
        for row in r["rows"]:
            marca = " <-- ITEM VERIFICADO!" if row[0] == ITEM_VERIFICAR else ""
            if row[0] == ITEM_VERIFICAR:
                tem_446518 = True
            print(f"  {row[0]:>10} | {row[2]:>8} | {str(row[3]):>12} | {str(row[1])[:30]}{marca}")

        if tem_446518:
            print(f"\n  >>> ITEM {ITEM_VERIFICAR} CONFIRMADO no pedido 1192208! <<<")
        else:
            print(f"\n  !!! ITEM {ITEM_VERIFICAR} NAO ENCONTRADO no pedido 1192208 !!!")
    else:
        print("\n  Pedido 1192208 nao tem itens ou nao existe")

    # ========================================
    # RESUMO FINAL
    # ========================================
    print("\n" + "=" * 80)
    print("RESUMO E RECOMENDACOES")
    print("=" * 80)
    print("""
SITUACAO IDENTIFICADA:
----------------------
1. Pedido 1183490 foi CANCELADO mas os EMPENHOS nao foram liberados
2. Pedido 1192177 nao consegue empenhar alguns itens porque ja estao
   empenhados no pedido cancelado
3. Pedido 1192208 foi criado para itens sem estoque

ACAO RECOMENDADA:
-----------------
* Liberar os empenhos do pedido CANCELADO (1183490)
* Isso permitira que o pedido 1192177 empenhe os itens necessarios
* Verificar no Sankhya: Central de Empenho ou Gestao de Pedidos

COMO LIBERAR EMPENHO DO PEDIDO CANCELADO:
-----------------------------------------
Opcao 1: Via tela do Sankhya
  - Acessar Central de Empenho
  - Buscar pedido 1183490
  - Cancelar/Liberar empenhos

Opcao 2: Via SQL (CUIDADO - fazer backup antes!)
  DELETE FROM TGWEMPE WHERE NUNOTAPEDVEN = 1183490;
""")

if __name__ == "__main__":
    main()
