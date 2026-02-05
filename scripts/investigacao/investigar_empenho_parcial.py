# -*- coding: utf-8 -*-
"""
Investigar empenho parcial - Pedido 1181756
Item 159850: 9pc pedidas, 4pc empenhadas, 5pc faltantes
Questao: Sistema deveria gerar pedido para as 5pc faltantes?
"""

import os
import requests
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(project_root, 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

BASE_URL = "https://api.sankhya.com.br"

PEDIDO = 1181756
ITEM = 159850


def autenticar():
    auth_response = requests.post(
        f"{BASE_URL}/authenticate",
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
            f"{BASE_URL}/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
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
    print(f"INVESTIGAR EMPENHO PARCIAL - PEDIDO {PEDIDO}")
    print(f"Item {ITEM}: 9pc pedidas, 4pc empenhadas, 5pc faltantes")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!\n")

    # ========================================
    # 1. STATUS DO PEDIDO
    # ========================================
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
        c.TIPMOV,
        c.CODTIPOPER,
        t.DESCROPER,
        (SELECT COUNT(*) FROM TGFITE i WHERE i.NUNOTA = c.NUNOTA) AS QTD_ITENS
    FROM TGFCAB c
    LEFT JOIN TGFPAR p ON p.CODPARC = c.CODPARC
    LEFT JOIN TGFTOP t ON t.CODTIPOPER = c.CODTIPOPER AND t.DHALTER = (
        SELECT MAX(t2.DHALTER) FROM TGFTOP t2 WHERE t2.CODTIPOPER = c.CODTIPOPER
    )
    WHERE c.NUNOTA = {PEDIDO}
    """
    r1 = executar_query(access_token, query1, f"1. STATUS DO PEDIDO {PEDIDO}")
    if r1 and r1.get("rows"):
        row = r1["rows"][0]
        print(f"""
  NUNOTA: {row[0]}
  NUMNOTA: {row[1]}
  EMPRESA: {row[2]}
  CLIENTE: {row[4]}
  DATA: {str(row[5])[:10]}
  VALOR: R$ {row[6]:,.2f}
  PENDENTE: {row[7]}
  STATUSNOTA: {row[8]}
  TIPMOV: {row[9]}
  TOP: {row[10]} - {row[11]}
  QTD_ITENS: {row[12]}
""")

    # ========================================
    # 2. ITEM 159850 NO PEDIDO
    # ========================================
    query2 = f"""
    SELECT
        i.NUNOTA,
        i.CODPROD,
        p.DESCRPROD,
        i.QTDNEG,
        i.VLRUNIT,
        i.VLRTOT,
        i.PENDENTE,
        i.STATUSNOTA,
        i.SEQUENCIA
    FROM TGFITE i
    LEFT JOIN TGFPRO p ON p.CODPROD = i.CODPROD
    WHERE i.NUNOTA = {PEDIDO} AND i.CODPROD = {ITEM}
    """
    r2 = executar_query(access_token, query2, f"2. ITEM {ITEM} NO PEDIDO")
    if r2 and r2.get("rows"):
        row = r2["rows"][0]
        print(f"""
  CODPROD: {row[1]}
  PRODUTO: {row[2]}
  QTDNEG: {row[3]}
  VLRUNIT: R$ {row[4]}
  VLRTOT: R$ {row[5]}
  PENDENTE: {row[6]}
  STATUSNOTA: {row[7]}
  SEQUENCIA: {row[8]}
""")
    else:
        print(f"\n  Item {ITEM} NAO encontrado no pedido {PEDIDO}!")

    # ========================================
    # 3. EMPENHOS DO ITEM NO PEDIDO
    # ========================================
    query3 = f"""
    SELECT
        e.NUNOTAPEDVEN,
        e.NUNOTA AS NUNOTA_COMPRA,
        e.CODPROD,
        e.QTDEMPENHO,
        e.PENDENTE,
        c.NUMNOTA AS NF_COMPRA,
        c.STATUSNOTA AS STATUS_COMPRA
    FROM TGWEMPE e
    LEFT JOIN TGFCAB c ON c.NUNOTA = e.NUNOTA
    WHERE e.NUNOTAPEDVEN = {PEDIDO} AND e.CODPROD = {ITEM}
    """
    r3 = executar_query(access_token, query3, f"3. EMPENHOS DO ITEM {ITEM}")
    if r3 and r3.get("rows"):
        total_emp = 0
        print(f"\n  {'COMPRA':>10} | {'QTDEMP':>8} | {'PENDENTE':>8} | STATUS")
        print("  " + "-" * 50)
        for row in r3["rows"]:
            total_emp += row[3] or 0
            print(f"  {row[1]:>10} | {row[3]:>8} | {str(row[4]):>8} | {row[6]}")
        print(f"\n  TOTAL EMPENHADO: {total_emp} pc")
        print(f"  FALTAM EMPENHAR: {9 - total_emp} pc")
    else:
        print(f"\n  Nenhum empenho encontrado para item {ITEM} no pedido {PEDIDO}")

    # ========================================
    # 4. ESTOQUE ATUAL DO ITEM
    # ========================================
    query4 = f"""
    SELECT
        e.CODEMP,
        e.CODLOCAL,
        l.DESCRLOCAL,
        e.ESTOQUE,
        e.RESERVADO,
        e.ESTOQUE - NVL(e.RESERVADO, 0) AS DISPONIVEL
    FROM TGFEST e
    LEFT JOIN TGFLOC l ON l.CODLOCAL = e.CODLOCAL AND l.CODEMP = e.CODEMP
    WHERE e.CODPROD = {ITEM}
      AND e.ESTOQUE > 0
    ORDER BY e.CODEMP, e.CODLOCAL
    """
    r4 = executar_query(access_token, query4, f"4. ESTOQUE ATUAL DO ITEM {ITEM}")
    if r4 and r4.get("rows"):
        print(f"\n  {'EMP':>5} | {'LOCAL':>8} | {'ESTOQUE':>10} | {'RESERV':>8} | {'DISP':>8} | DESCRICAO")
        print("  " + "-" * 70)
        total_est = 0
        total_disp = 0
        for row in r4["rows"]:
            total_est += row[3] or 0
            total_disp += row[5] or 0
            print(f"  {row[0]:>5} | {row[1]:>8} | {row[3]:>10} | {row[4] or 0:>8} | {row[5] or 0:>8} | {str(row[2])[:25]}")
        print(f"\n  TOTAL ESTOQUE: {total_est}")
        print(f"  TOTAL DISPONIVEL: {total_disp}")
    else:
        print(f"\n  Nenhum estoque encontrado para item {ITEM}")

    # ========================================
    # 5. SOLICITACOES DE COMPRA DO ITEM
    # ========================================
    query5 = f"""
    SELECT
        s.NUSOLICITACAO,
        s.NUNOTA AS NUNOTA_ORIGEM,
        s.CODPROD,
        s.QTDSOLICITADA,
        s.QTDATENDIDA,
        s.DTSOLICITACAO,
        s.STATUSSOLICITACAO,
        s.OBSERVACAO
    FROM TGWSOL s
    WHERE s.CODPROD = {ITEM}
      AND s.DTSOLICITACAO >= SYSDATE - 30
    ORDER BY s.DTSOLICITACAO DESC
    """
    r5 = executar_query(access_token, query5, f"5. SOLICITACOES DE COMPRA DO ITEM {ITEM} (ultimos 30 dias)")
    if r5 and r5.get("rows"):
        print(f"\n  {'NUSOLICIT':>10} | {'ORIGEM':>10} | {'QTDSOL':>8} | {'QTDATEND':>8} | {'STATUS':>8} | DATA")
        print("  " + "-" * 70)
        for row in r5["rows"]:
            print(f"  {row[0]:>10} | {row[1] or '-':>10} | {row[3]:>8} | {row[4] or 0:>8} | {str(row[6]):>8} | {str(row[5])[:10]}")
    else:
        print(f"\n  Nenhuma solicitacao de compra encontrada")

    # ========================================
    # 6. VERIFICAR SOLICITACAO PELO PEDIDO
    # ========================================
    query6 = f"""
    SELECT
        s.NUSOLICITACAO,
        s.NUNOTA,
        s.CODPROD,
        s.QTDSOLICITADA,
        s.QTDATENDIDA,
        s.DTSOLICITACAO,
        s.STATUSSOLICITACAO
    FROM TGWSOL s
    WHERE s.NUNOTA = {PEDIDO}
    ORDER BY s.CODPROD
    """
    r6 = executar_query(access_token, query6, f"6. SOLICITACOES GERADAS PELO PEDIDO {PEDIDO}")
    if r6 and r6.get("rows"):
        print(f"\n  {len(r6['rows'])} solicitacoes encontradas:")
        print(f"\n  {'NUSOLICIT':>10} | {'CODPROD':>10} | {'QTDSOL':>8} | {'QTDATEND':>8} | STATUS")
        print("  " + "-" * 60)
        for row in r6["rows"]:
            marca = " <-- ITEM!" if row[2] == ITEM else ""
            print(f"  {row[0]:>10} | {row[2]:>10} | {row[3]:>8} | {row[4] or 0:>8} | {row[6]}{marca}")
    else:
        print(f"\n  Nenhuma solicitacao gerada pelo pedido {PEDIDO}")

    # ========================================
    # 7. COTACOES DO ITEM
    # ========================================
    query7 = f"""
    SELECT
        c.NUCOTACAO,
        c.NUSOLICITACAO,
        c.CODPROD,
        c.QTDCOTADA,
        c.DTCOTACAO,
        c.STATUSCOTACAO
    FROM TGWCOT c
    WHERE c.CODPROD = {ITEM}
      AND c.DTCOTACAO >= SYSDATE - 30
    ORDER BY c.DTCOTACAO DESC
    """
    r7 = executar_query(access_token, query7, f"7. COTACOES DO ITEM {ITEM} (ultimos 30 dias)")
    if r7 and r7.get("rows"):
        print(f"\n  {'NUCOT':>10} | {'NUSOLICIT':>10} | {'QTDCOT':>8} | STATUS | DATA")
        print("  " + "-" * 60)
        for row in r7["rows"]:
            print(f"  {row[0]:>10} | {row[1] or '-':>10} | {row[3]:>8} | {row[5]} | {str(row[4])[:10]}")
    else:
        print(f"\n  Nenhuma cotacao encontrada")

    # ========================================
    # 8. PEDIDOS DERIVADOS/RELACIONADOS
    # ========================================
    query8 = f"""
    SELECT
        c.NUNOTA,
        c.NUMNOTA,
        c.DTNEG,
        c.CODTIPOPER,
        t.DESCROPER,
        c.STATUSNOTA,
        c.PENDENTE,
        (SELECT SUM(i.QTDNEG) FROM TGFITE i WHERE i.NUNOTA = c.NUNOTA AND i.CODPROD = {ITEM}) AS QTD_ITEM
    FROM TGFCAB c
    LEFT JOIN TGFTOP t ON t.CODTIPOPER = c.CODTIPOPER AND t.DHALTER = (
        SELECT MAX(t2.DHALTER) FROM TGFTOP t2 WHERE t2.CODTIPOPER = c.CODTIPOPER
    )
    WHERE c.NUNOTAORIG = {PEDIDO}
       OR c.AD_NUNOTAORIG = {PEDIDO}
    ORDER BY c.NUNOTA
    """
    r8 = executar_query(access_token, query8, f"8. PEDIDOS DERIVADOS DO {PEDIDO}")
    if r8 and r8.get("rows"):
        print(f"\n  {len(r8['rows'])} pedidos derivados:")
        print(f"\n  {'NUNOTA':>10} | {'DATA':<12} | {'TOP':<6} | {'STATUS':>8} | QTD_ITEM | DESCRICAO")
        print("  " + "-" * 80)
        for row in r8["rows"]:
            print(f"  {row[0]:>10} | {str(row[2])[:10]:<12} | {row[3]:<6} | {str(row[5]):>8} | {row[7] or '-':>8} | {str(row[4])[:30]}")
    else:
        print(f"\n  Nenhum pedido derivado encontrado")

    # ========================================
    # 9. VERIFICAR NA TGWPED (Pedido WMS)
    # ========================================
    query9 = f"""
    SELECT * FROM TGWPED
    WHERE NUNOTA = {PEDIDO}
       OR NUNOTAORIG = {PEDIDO}
    """
    r9 = executar_query(access_token, query9, f"9. TGWPED - Pedidos WMS relacionados")
    if r9 and r9.get("rows"):
        fields = r9.get("fieldsMetadata", [])
        print(f"\n  {len(r9['rows'])} registros encontrados")
        for i, row in enumerate(r9["rows"][:5]):
            print(f"\n  Registro {i+1}:")
            for j, f in enumerate(fields):
                print(f"    {f['name']}: {row[j]}")
    else:
        print(f"\n  Nenhum registro na TGWPED")

    # ========================================
    # 10. HISTORICO DE MOVIMENTACOES DO ITEM NO PEDIDO
    # ========================================
    query10 = f"""
    SELECT
        m.DTMOV,
        m.CODPROD,
        m.QTDMOV,
        m.TIPMOV,
        m.NUNOTA,
        m.HISTORICO
    FROM TGFMOV m
    WHERE m.CODPROD = {ITEM}
      AND m.NUNOTA = {PEDIDO}
    ORDER BY m.DTMOV DESC
    """
    r10 = executar_query(access_token, query10, f"10. MOVIMENTACOES DO ITEM {ITEM} NO PEDIDO")
    if r10 and r10.get("rows"):
        print(f"\n  {'DATA':<12} | {'QTDMOV':>8} | {'TIPMOV':>6} | HISTORICO")
        print("  " + "-" * 60)
        for row in r10["rows"]:
            print(f"  {str(row[0])[:10]:<12} | {row[2]:>8} | {str(row[3]):>6} | {str(row[5])[:30] if row[5] else '-'}")
    else:
        print(f"\n  Nenhuma movimentacao encontrada")

    # ========================================
    # RESUMO
    # ========================================
    print("\n" + "=" * 80)
    print("RESUMO DA INVESTIGACAO")
    print("=" * 80)
    print(f"""
SITUACAO:
---------
- Pedido {PEDIDO} tem item {ITEM} com 9 pecas
- Estoque tinha apenas 4 pecas disponiveis
- Usuario empenhou as 4 pecas via tela "Empenho Produto"

QUESTAO:
--------
O sistema deveria gerar automaticamente um pedido/solicitacao
para as 5 pecas faltantes?

VERIFICAR NOS RESULTADOS ACIMA:
-------------------------------
1. Se existe SOLICITACAO DE COMPRA (TGWSOL) para as 5 pecas
2. Se existe COTACAO (TGWCOT) para o item
3. Se existe PEDIDO DERIVADO (NUNOTAORIG ou AD_NUNOTAORIG)
4. Se o item tem quantidade PENDENTE no pedido

SE NAO GEROU:
-------------
Pode ser configuracao da TOP ou parametro do sistema.
Verificar na tela de configuracao de empenho se existe opcao
para "Gerar solicitacao automatica para faltantes".
""")


if __name__ == "__main__":
    main()
