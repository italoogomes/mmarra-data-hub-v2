# -*- coding: utf-8 -*-
"""
Investiga as tabelas da query de precos/excecoes
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
    print("[1] Autenticando...")
    auth_response = requests.post(
        "https://api.sankhya.com.br/authenticate",
        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Token": X_TOKEN},
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
        timeout=30
    )
    if auth_response.status_code != 200:
        return None
    print("[OK] Token obtido!")
    return auth_response.json()["access_token"]

def executar_query(access_token, query_sql, descricao=""):
    print(f"\n[QUERY] {descricao}")
    print("-" * 60)
    query_payload = {"requestBody": {"sql": query_sql}}
    try:
        query_response = requests.post(
            "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=query_payload,
            timeout=60
        )
        if query_response.status_code != 200:
            print(f"[ERRO] {query_response.text}")
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
    print("ANALISE DAS TABELAS: TGFNTA, TGFTAB, TGFEXC")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    # 1. Estrutura TGFNTA
    query1 = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH
    FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = 'TGFNTA'
    ORDER BY COLUMN_ID
    """
    r1 = executar_query(access_token, query1, "Estrutura TGFNTA")
    if r1 and r1.get("rows"):
        print("\nColunas TGFNTA:")
        for row in r1["rows"][:15]:
            print(f"  - {row[0]} ({row[1]})")

    # 2. Estrutura TGFTAB
    query2 = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH
    FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = 'TGFTAB'
    ORDER BY COLUMN_ID
    """
    r2 = executar_query(access_token, query2, "Estrutura TGFTAB")
    if r2 and r2.get("rows"):
        print("\nColunas TGFTAB:")
        for row in r2["rows"][:15]:
            print(f"  - {row[0]} ({row[1]})")

    # 3. Estrutura TGFEXC
    query3 = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH
    FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = 'TGFEXC'
    ORDER BY COLUMN_ID
    """
    r3 = executar_query(access_token, query3, "Estrutura TGFEXC")
    if r3 and r3.get("rows"):
        print("\nColunas TGFEXC:")
        for row in r3["rows"][:15]:
            print(f"  - {row[0]} ({row[1]})")

    # 4. Contar registros
    print("\n" + "=" * 60)
    print("CONTAGEM DE REGISTROS")
    print("=" * 60)

    for tabela in ['TGFNTA', 'TGFTAB', 'TGFEXC']:
        query = f"SELECT COUNT(*) FROM {tabela}"
        r = executar_query(access_token, query, f"Contando {tabela}")
        if r and r.get("rows"):
            print(f"  {tabela}: {r['rows'][0][0]:,} registros")

    # 5. Ver o que e CODTAB 9851
    query5 = """
    SELECT * FROM TGFNTA WHERE CODTAB = 9851
    """
    r5 = executar_query(access_token, query5, "Dados TGFNTA para CODTAB=9851")
    if r5 and r5.get("rows"):
        fields = r5.get("fieldsMetadata", [])
        print("\nDados encontrados:")
        for i, field in enumerate(fields[:10]):
            val = r5["rows"][0][i] if r5["rows"] else None
            print(f"  {field['name']}: {val}")

    # 6. Ver TGFTAB para CODTAB 9851
    query6 = """
    SELECT NUTAB, CODTAB, DTVIGOR, DESCRTAB
    FROM TGFTAB
    WHERE CODTAB = 9851
    ORDER BY DTVIGOR DESC
    FETCH FIRST 5 ROWS ONLY
    """
    r6 = executar_query(access_token, query6, "TGFTAB para CODTAB=9851")
    if r6 and r6.get("rows"):
        print("\nVersoes da tabela 9851:")
        print(f"{'NUTAB':>10} | {'CODTAB':>8} | {'DTVIGOR':<12} | DESCRTAB")
        print("-" * 60)
        for row in r6["rows"]:
            print(f"{row[0]:>10} | {row[1]:>8} | {str(row[2])[:10]:<12} | {str(row[3])[:30]}")

    # 7. Ver TGFEXC para NUTAB 32
    query7 = """
    SELECT NUTAB, CODPROD, VLRVENDA, PERCDESC, CODPARC
    FROM TGFEXC
    WHERE NUTAB = 32
    FETCH FIRST 10 ROWS ONLY
    """
    r7 = executar_query(access_token, query7, "TGFEXC para NUTAB=32")
    if r7 and r7.get("rows"):
        print("\nExcecoes da tabela (NUTAB=32):")
        print(f"{'NUTAB':>8} | {'CODPROD':>10} | {'VLRVENDA':>12} | {'PERCDESC':>10} | {'CODPARC':>10}")
        print("-" * 60)
        for row in r7["rows"]:
            print(f"{row[0]:>8} | {row[1]:>10} | {str(row[2]):>12} | {str(row[3]):>10} | {str(row[4]):>10}")

    # 8. Executar a query original
    query8 = """
    select TT.NUTAB, TT.CODTAB, TT.DTVIGOR, TT.DESCRTAB,
           TE.CODPROD, TE.VLRVENDA, TE.PERCDESC
    from TgfNta TN
      left join TgfTab TT on TT.CodTab = TN.CodTab
                         and TT.DtVigor = (Select Max(TT2.DtVigor)
                                           from TgfTab TT2
                                           where TT2.CodTab = TN.CodTab)
      left join TgfExc TE on TE.NuTab = TT.NuTab
    where TN.CodTab = 9851 and TT.NuTab = 32
    FETCH FIRST 20 ROWS ONLY
    """
    r8 = executar_query(access_token, query8, "Query ORIGINAL")
    if r8 and r8.get("rows"):
        print("\nResultado da query:")
        print(f"{'NUTAB':>8} | {'CODTAB':>8} | {'DTVIGOR':<12} | {'CODPROD':>10} | {'VLRVENDA':>12}")
        print("-" * 60)
        for row in r8["rows"][:10]:
            print(f"{row[0]:>8} | {row[1]:>8} | {str(row[2])[:10]:<12} | {str(row[4]):>10} | {str(row[5]):>12}")

    print("\n" + "=" * 80)
    print("ANALISE CONCLUIDA!")
    print("=" * 80)

if __name__ == "__main__":
    main()
