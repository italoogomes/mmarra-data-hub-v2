# -*- coding: utf-8 -*-
"""
Investigar Views de empenho e a estrutura da query
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
    auth_response = requests.post(
        f"{BASE_URL}/authenticate",
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
    print("INVESTIGAR VIEW DE EMPENHO E ESTRUTURA")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    print("[OK] Autenticado!\n")

    # 1. Ver codigo da View VW_PERCENTUAL_EMPENHO_ATENDIDO
    print("=" * 80)
    print("[1] CODIGO DA VIEW VW_PERCENTUAL_EMPENHO_ATENDIDO")
    print("=" * 80)

    query_view = """
    SELECT TEXT
    FROM ALL_VIEWS
    WHERE VIEW_NAME = 'VW_PERCENTUAL_EMPENHO_ATENDIDO'
    """
    result = executar_query(access_token, query_view)
    if result and result.get("rows"):
        texto = result["rows"][0][0]
        print(texto)
    else:
        print("  View nao encontrada")

    # 2. Verificar se TGFITE.CODEMP eh usado em alguma View de empenho
    print("\n" + "=" * 80)
    print("[2] VERIFICAR CAMPOS CODEMP NAS VIEWS")
    print("=" * 80)

    query_codemp = """
    SELECT VIEW_NAME, TEXT
    FROM ALL_VIEWS
    WHERE TEXT LIKE '%CODEMP%'
      AND (VIEW_NAME LIKE '%EMPE%' OR VIEW_NAME LIKE '%WMS%')
    """
    result = executar_query(access_token, query_codemp)
    if result and result.get("rows"):
        for row in result["rows"]:
            print(f"\n--- {row[0]} ---")
            print(row[1][:500] if row[1] else 'NULL')
    else:
        print("  Nenhuma view encontrada com CODEMP")

    # 3. Estrutura completa da TGWEMPE (tabela de empenho)
    print("\n" + "=" * 80)
    print("[3] ESTRUTURA COMPLETA DA TGWEMPE")
    print("=" * 80)

    query_estrutura = """
    SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGWEMPE'
    ORDER BY COLUMN_ID
    """
    result = executar_query(access_token, query_estrutura)
    if result and result.get("rows"):
        print(f"{'COLUNA':<25} | {'TIPO':<15} | {'NULLABLE'}")
        print("-" * 50)
        for row in result["rows"]:
            print(f"{row[0]:<25} | {row[1]:<15} | {row[2]}")

    # 4. Verificar se TGWEMPE tem CODEMP
    print("\n" + "=" * 80)
    print("[4] VERIFICAR SE TGWEMPE TEM CODEMP")
    print("=" * 80)

    query_empe_codemp = """
    SELECT COLUMN_NAME
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGWEMPE'
      AND COLUMN_NAME = 'CODEMP'
    """
    result = executar_query(access_token, query_empe_codemp)
    if result and result.get("rows"):
        print("  [SIM] TGWEMPE TEM CODEMP!")
    else:
        print("  [NAO] TGWEMPE NAO TEM CODEMP diretamente")
        print("  O CODEMP vem via JOIN com TGFCAB")

    # 5. Ver como TGWEMPE se relaciona com TGFCAB
    print("\n" + "=" * 80)
    print("[5] RELACIONAMENTO TGWEMPE -> TGFCAB")
    print("=" * 80)

    query_rel = """
    SELECT
        'TGWEMPE.NUNOTA' as CAMPO_EMPE,
        'TGFCAB.NUNOTA' as CAMPO_CAB,
        'INNER JOIN TGFCAB CAB ON EMPE.NUNOTA = CAB.NUNOTA' as JOIN_SUGERIDO
    FROM DUAL
    """
    result = executar_query(access_token, query_rel)
    if result and result.get("rows"):
        print("  Relacionamento: TGWEMPE.NUNOTA -> TGFCAB.NUNOTA")
        print("  JOIN: TGWEMPE EMPE INNER JOIN TGFCAB CAB ON EMPE.NUNOTA = CAB.NUNOTA")
        print("  Assim: CAB.CODEMP pode ser usado para filtrar")

    # 6. Exemplo de query que FUNCIONA com filtro CODEMP
    print("\n" + "=" * 80)
    print("[6] EXEMPLO DE QUERY COM FILTRO CODEMP (CORRETA)")
    print("=" * 80)

    query_exemplo = """
    SELECT
        EMPE.NUNOTA,
        EMPE.CODPROD,
        EMPE.NUNOTAPEDVEN,
        EMPE.QTDEMPENHO,
        CAB.CODEMP,
        EMP.NOMEFANTASIA as EMPRESA
    FROM TGWEMPE EMPE
    INNER JOIN TGFCAB CAB ON EMPE.NUNOTA = CAB.NUNOTA
    INNER JOIN TSIEMP EMP ON CAB.CODEMP = EMP.CODEMP
    WHERE CAB.CODEMP = 1
      AND ROWNUM <= 5
    """
    print("  Query exemplo:")
    print(query_exemplo)

    result = executar_query(access_token, query_exemplo)
    if result and result.get("rows"):
        print("\n  Resultado:")
        fields = result.get("fieldsMetadata", [])
        field_names = [f["name"] for f in fields]
        print(f"  {' | '.join(field_names)}")
        for row in result["rows"]:
            valores = [str(v)[:20] if v else 'NULL' for v in row]
            print(f"  {' | '.join(valores)}")

    # 7. Verificar se existe View customizavel no WMS
    print("\n" + "=" * 80)
    print("[7] VIEWS WMS QUE PODEM SER CUSTOMIZADAS")
    print("=" * 80)

    query_views_wms = """
    SELECT VIEW_NAME, TEXT_LENGTH
    FROM ALL_VIEWS
    WHERE VIEW_NAME LIKE 'VGW%'
    ORDER BY VIEW_NAME
    """
    result = executar_query(access_token, query_views_wms)
    if result and result.get("rows"):
        for row in result["rows"]:
            print(f"  {row[0]}: {row[1]} chars")

    # 8. Ver codigo de uma View VGW para entender o padrao
    print("\n" + "=" * 80)
    print("[8] EXEMPLO: CODIGO DA VGWSTATUSWMS")
    print("=" * 80)

    query_vgw = """
    SELECT TEXT
    FROM ALL_VIEWS
    WHERE VIEW_NAME = 'VGWSTATUSWMS'
    """
    result = executar_query(access_token, query_vgw)
    if result and result.get("rows"):
        texto = result["rows"][0][0]
        print(texto[:2000] if len(texto) > 2000 else texto)

    print("\n" + "=" * 80)
    print("CONCLUSAO")
    print("=" * 80)
    print("""
DESCOBERTAS:
1. TGWEMPE NAO tem CODEMP diretamente
2. TGFITE TEM CODEMP (descoberto antes)
3. O filtro CODEMP deve vir via JOIN com TGFCAB

PROBLEMA NO SANKHYA:
- A query 'buscaPossiveisEmpenhoProdVenda' NAO faz o JOIN correto
- A query 'buscaPossiveisProdutosParaEmpenho' (compras) FAZ o JOIN

SOLUCAO POSSIVEL:
1. Criar uma VIEW customizada que ja inclua o CODEMP
2. Ou abrir chamado no suporte Sankhya para corrigir o bug
""")


if __name__ == "__main__":
    main()
