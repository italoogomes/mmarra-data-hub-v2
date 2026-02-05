# -*- coding: utf-8 -*-
"""
Investigar a estrutura da tela Empenho de Produtos
Verificar se usa Views, qual a configuracao da tela, etc.
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

BASE_URL = "https://api.sankhya.com.br"


def autenticar():
    """Autentica e retorna o access_token"""
    auth_response = requests.post(
        f"{BASE_URL}/authenticate",
        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Token": X_TOKEN},
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
        timeout=30
    )
    if auth_response.status_code != 200:
        print(f"[ERRO] Autenticacao falhou: {auth_response.status_code}")
        return None
    return auth_response.json()["access_token"]


def executar_query(access_token, query_sql):
    """Executa uma query SELECT"""
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


def mostrar_resultado(result, titulo=""):
    """Mostra resultado de uma query"""
    if not result or not result.get("rows"):
        print(f"  (nenhum resultado)")
        return []

    fields = result.get("fieldsMetadata", [])
    field_names = [f["name"] for f in fields]

    # Mostrar cabecalho
    print(f"  {' | '.join(field_names)}")
    print(f"  {'-' * 80}")

    registros = []
    for row in result["rows"][:20]:  # Limitar a 20 registros
        registro = dict(zip(field_names, row))
        registros.append(registro)
        valores = [str(v)[:30] if v else 'NULL' for v in row]
        print(f"  {' | '.join(valores)}")

    if len(result["rows"]) > 20:
        print(f"  ... e mais {len(result['rows']) - 20} registros")

    return registros


def main():
    print("=" * 80)
    print("INVESTIGAR TELA EMPENHO DE PRODUTOS")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    print("[OK] Autenticado!\n")

    # 1. Buscar Views relacionadas a empenho
    print("=" * 80)
    print("[1] VIEWS RELACIONADAS A EMPENHO")
    print("=" * 80)

    query_views = """
    SELECT VIEW_NAME, TEXT_LENGTH
    FROM ALL_VIEWS
    WHERE UPPER(VIEW_NAME) LIKE '%EMPE%'
       OR UPPER(VIEW_NAME) LIKE '%WMS%'
    ORDER BY VIEW_NAME
    """
    result = executar_query(access_token, query_views)
    mostrar_resultado(result)

    # 2. Buscar tabelas do dicionario Sankhya relacionadas a empenho
    print("\n" + "=" * 80)
    print("[2] TABELAS DO DICIONARIO (TDDTAB) RELACIONADAS A EMPENHO")
    print("=" * 80)

    query_tddtab = """
    SELECT NOMETAB, DESCRUSUSIMPL, ABORIG
    FROM TDDTAB
    WHERE UPPER(NOMETAB) LIKE '%EMPE%'
       OR UPPER(DESCRUSUSIMPL) LIKE '%EMPENHO%'
    ORDER BY NOMETAB
    """
    result = executar_query(access_token, query_tddtab)
    mostrar_resultado(result)

    # 3. Buscar configuracao da tela de empenho
    print("\n" + "=" * 80)
    print("[3] CONFIGURACAO DE TELAS (TDDTELA) RELACIONADAS A EMPENHO")
    print("=" * 80)

    query_tela = """
    SELECT NUCAMPO, NOMETELA, DESCTELA, TIPOTELA
    FROM TDDTELA
    WHERE UPPER(NOMETELA) LIKE '%EMPE%'
       OR UPPER(DESCTELA) LIKE '%EMPENHO%'
    ORDER BY NOMETELA
    """
    result = executar_query(access_token, query_tela)
    mostrar_resultado(result)

    # 4. Buscar instancias de tela
    print("\n" + "=" * 80)
    print("[4] INSTANCIAS DE TELA (TSIINS) RELACIONADAS A EMPENHO")
    print("=" * 80)

    query_inst = """
    SELECT NUINS, DESCRICAO, ENTPRINCIPAL, RESOURCEID
    FROM TSIINS
    WHERE UPPER(DESCRICAO) LIKE '%EMPE%'
       OR UPPER(ENTPRINCIPAL) LIKE '%EMPE%'
    ORDER BY NUINS
    """
    result = executar_query(access_token, query_inst)
    instancias = mostrar_resultado(result)

    # 5. Se encontrou instancias, buscar detalhes
    if instancias:
        print("\n" + "=" * 80)
        print("[5] DETALHES DAS INSTANCIAS ENCONTRADAS")
        print("=" * 80)

        for inst in instancias[:5]:
            nuins = inst.get('NUINS')
            print(f"\n--- NUINS: {nuins} - {inst.get('DESCRICAO')} ---")

            # Buscar configuracao da instancia
            query_config = f"""
            SELECT CHAVE, VALOR
            FROM TSIINSCONFIG
            WHERE NUINS = {nuins}
            ORDER BY CHAVE
            """
            result = executar_query(access_token, query_config)
            if result and result.get("rows"):
                for row in result["rows"][:10]:
                    chave = row[0] or ''
                    valor = str(row[1])[:50] if row[1] else 'NULL'
                    print(f"  {chave}: {valor}")

    # 6. Buscar servicos de empenho cadastrados
    print("\n" + "=" * 80)
    print("[6] SERVICOS CADASTRADOS (TSISER) RELACIONADOS A EMPENHO")
    print("=" * 80)

    query_servico = """
    SELECT CODSER, DESCRSER, NOMECLASSE
    FROM TSISER
    WHERE UPPER(DESCRSER) LIKE '%EMPE%'
       OR UPPER(NOMECLASSE) LIKE '%Empenho%'
    ORDER BY CODSER
    """
    result = executar_query(access_token, query_servico)
    mostrar_resultado(result)

    # 7. Buscar especificamente a View VGW_EMPE se existir
    print("\n" + "=" * 80)
    print("[7] VERIFICAR SE EXISTE VIEW VGW_EMPE OU SIMILAR")
    print("=" * 80)

    query_vgw = """
    SELECT OBJECT_NAME, OBJECT_TYPE
    FROM ALL_OBJECTS
    WHERE OBJECT_NAME LIKE 'VGW%'
       OR OBJECT_NAME LIKE 'V_EMPE%'
       OR OBJECT_NAME LIKE 'VW_EMPE%'
    ORDER BY OBJECT_NAME
    """
    result = executar_query(access_token, query_vgw)
    mostrar_resultado(result)

    # 8. Buscar campos da TGFITE que possam ter CODEMP
    print("\n" + "=" * 80)
    print("[8] CAMPOS DA TGFITE (ITEM NOTA)")
    print("=" * 80)

    query_campos = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGFITE'
      AND (COLUMN_NAME LIKE '%EMP%' OR COLUMN_NAME LIKE '%CAB%')
    ORDER BY COLUMN_NAME
    """
    result = executar_query(access_token, query_campos)
    mostrar_resultado(result)

    # 9. Buscar configuracao de filtros de tela (TSIEVE)
    print("\n" + "=" * 80)
    print("[9] FILTROS DE TELA (TSIEVE) PARA EMPENHO")
    print("=" * 80)

    query_filtros = """
    SELECT NUEVE, DESCRICAO, ENTIDADE, EXPRESSAO
    FROM TSIEVE
    WHERE UPPER(DESCRICAO) LIKE '%EMPE%'
       OR UPPER(ENTIDADE) LIKE '%EMPE%'
    ORDER BY NUEVE
    """
    result = executar_query(access_token, query_filtros)
    mostrar_resultado(result)

    # 10. Tentar encontrar o codigo da tela de Empenho de Produtos
    print("\n" + "=" * 80)
    print("[10] BUSCAR TELA 'EMPENHO DE PRODUTOS' POR DESCRICAO EXATA")
    print("=" * 80)

    query_tela_exata = """
    SELECT *
    FROM TSIINS
    WHERE UPPER(DESCRICAO) LIKE '%EMPENHO%PRODUTO%'
       OR UPPER(DESCRICAO) = 'EMPENHO DE PRODUTOS'
       OR RESOURCEID LIKE '%EmpenhoProduto%'
    """
    result = executar_query(access_token, query_tela_exata)
    mostrar_resultado(result)

    # 11. Buscar todas as entidades WMS
    print("\n" + "=" * 80)
    print("[11] ENTIDADES WMS NO DICIONARIO")
    print("=" * 80)

    query_wms = """
    SELECT NOMETAB, DESCRUSUSIMPL, ABORIG
    FROM TDDTAB
    WHERE NOMETAB LIKE 'TGW%'
    ORDER BY NOMETAB
    """
    result = executar_query(access_token, query_wms)
    mostrar_resultado(result)

    print("\n" + "=" * 80)
    print("CONCLUSAO")
    print("=" * 80)
    print("""
Com base nos resultados acima, podemos identificar:
1. Se existe uma View customizavel para a tela
2. A configuracao da instancia de tela
3. Possiveis pontos de customizacao

Se encontrarmos uma View, podemos sugerir criar uma View customizada
que inclua o filtro CODEMP.
""")


if __name__ == "__main__":
    main()
