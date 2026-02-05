# -*- coding: utf-8 -*-
"""
Investiga as tabelas da query de precos/excecoes - v2
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
    print(f"\n[QUERY] {descricao}")
    print("-" * 70)
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
    print("ANALISE DA QUERY DE PRECOS/EXCECOES")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return

    print("[OK] Autenticado!")

    # 1. Ver TGFTAB para CODTAB 9851 (sem DESCRTAB)
    query1 = """
    SELECT NUTAB, CODTAB, DTVIGOR, PERCENTUAL, FORMULA
    FROM TGFTAB
    WHERE CODTAB = 9851
    ORDER BY DTVIGOR DESC
    """
    r1 = executar_query(access_token, query1, "Versoes da tabela de preco 9851")
    if r1 and r1.get("rows"):
        print("\nVersoes encontradas:")
        print(f"{'NUTAB':>8} | {'CODTAB':>8} | {'DTVIGOR':<12} | {'PERCENTUAL':>10}")
        print("-" * 50)
        for row in r1["rows"]:
            print(f"{row[0]:>8} | {row[1]:>8} | {str(row[2])[:10]:<12} | {str(row[3]):>10}")

    # 2. Ver TGFEXC para NUTAB 32 (campos corretos)
    query2 = """
    SELECT NUTAB, CODPROD, CODLOCAL, VLRVENDA, PERCDESC, TIPO
    FROM TGFEXC
    WHERE NUTAB = 32
    FETCH FIRST 15 ROWS ONLY
    """
    r2 = executar_query(access_token, query2, "Excecoes de preco (NUTAB=32)")
    if r2 and r2.get("rows"):
        print("\nExcecoes encontradas:")
        print(f"{'NUTAB':>6} | {'CODPROD':>10} | {'LOCAL':>6} | {'VLRVENDA':>12} | {'PERCDESC':>10} | {'TIPO':<6}")
        print("-" * 65)
        for row in r2["rows"]:
            print(f"{row[0]:>6} | {row[1]:>10} | {str(row[2]):>6} | {str(row[3]):>12} | {str(row[4]):>10} | {str(row[5]):<6}")

    # 3. Executar a query original (ajustada)
    query3 = """
    select TT.NUTAB, TT.CODTAB, TT.DTVIGOR, TT.PERCENTUAL,
           TE.CODPROD, TE.VLRVENDA, TE.PERCDESC, TE.TIPO
    from TgfNta TN
      left join TgfTab TT on TT.CodTab = TN.CodTab
                         and TT.DtVigor = (Select Max(TT2.DtVigor)
                                           from TgfTab TT2
                                           where TT2.CodTab = TN.CodTab)
      left join TgfExc TE on TE.NuTab = TT.NuTab
    where TN.CodTab = 9851 and TT.NuTab = 32
    FETCH FIRST 20 ROWS ONLY
    """
    r3 = executar_query(access_token, query3, "Query ORIGINAL (ajustada)")
    if r3 and r3.get("rows"):
        print("\nResultado da query:")
        print(f"{'NUTAB':>6} | {'CODTAB':>6} | {'DTVIGOR':<10} | {'CODPROD':>10} | {'VLRVENDA':>12} | {'PERCDESC':>8}")
        print("-" * 70)
        for row in r3["rows"]:
            print(f"{row[0]:>6} | {row[1]:>6} | {str(row[2])[:10]:<10} | {str(row[4]):>10} | {str(row[5]):>12} | {str(row[6]):>8}")
        print(f"\nTotal de excecoes retornadas: {len(r3['rows'])}")

    # 4. Contar total de excecoes para NUTAB=32
    query4 = """
    SELECT COUNT(*) FROM TGFEXC WHERE NUTAB = 32
    """
    r4 = executar_query(access_token, query4, "Total de excecoes NUTAB=32")
    if r4 and r4.get("rows"):
        print(f"\nTotal de produtos com excecao: {r4['rows'][0][0]:,}")

    # 5. Entender o que e TGFNTA (nome da tabela de precos)
    query5 = """
    SELECT CODTAB, NOMETAB, ATIVO FROM TGFNTA ORDER BY CODTAB
    """
    r5 = executar_query(access_token, query5, "Todas as tabelas de preco (TGFNTA)")
    if r5 and r5.get("rows"):
        print("\nTabelas de preco cadastradas:")
        print(f"{'CODTAB':>8} | {'ATIVO':<5} | NOMETAB")
        print("-" * 60)
        for row in r5["rows"]:
            print(f"{row[0]:>8} | {row[1]:<5} | {str(row[2])[:40]}")

    print("\n" + "=" * 80)
    print("EXPLICACAO DA QUERY")
    print("=" * 80)
    print("""
A query busca EXCECOES DE PRECO para uma tabela de precos especifica.

ESTRUTURA:
----------
1. TGFNTA = Cadastro de Tabelas de Preco (header)
   - CODTAB = Codigo da tabela de preco
   - NOMETAB = Nome da tabela

2. TGFTAB = Versoes da Tabela de Preco (historico)
   - NUTAB = Numero unico da versao
   - CODTAB = FK para TGFNTA
   - DTVIGOR = Data de vigor da versao
   - Subquery pega a versao MAIS RECENTE (MAX DTVIGOR)

3. TGFEXC = Excecoes de Preco (precos especiais por produto)
   - NUTAB = FK para TGFTAB (versao da tabela)
   - CODPROD = Produto
   - VLRVENDA = Valor de venda especial
   - PERCDESC = Percentual de desconto
   - TIPO = Tipo da excecao

LOGICA:
-------
TGFNTA (tabela 9851)
    |
    +-- LEFT JOIN --> TGFTAB (versao mais recente por DTVIGOR)
                          |
                          +-- LEFT JOIN --> TGFEXC (excecoes de preco)

FILTROS:
--------
- TN.CodTab = 9851 --> Tabela de preco especifica
- TT.NuTab = 32 --> Versao especifica da tabela

RESULTADO:
----------
Retorna TODOS os produtos com excecao de preco na tabela 9851, versao 32.
Cada linha = um produto com preco/desconto especial.
""")

if __name__ == "__main__":
    main()
