# -*- coding: utf-8 -*-
"""
MAPEAMENTO COMPLETO DO BANCO SANKHYA
====================================
Varre todo o banco para descobrir:
- Todas as tabelas por modulo/prefixo
- Quantidade de registros
- Colunas principais
- Relacionamentos (FK)
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Carregar credenciais
env_path = os.path.join(os.path.dirname(__file__), 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

def autenticar():
    print("[1] Autenticando...")
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
        print(f"[ERRO] {auth_response.text}")
        return None
    print("[OK] Token obtido!")
    return auth_response.json()["access_token"]

def executar_query(access_token, query_sql, descricao="", silencioso=False):
    if not silencioso:
        print(f"  Executando: {descricao[:50]}...")

    query_payload = {"requestBody": {"sql": query_sql}}
    try:
        query_response = requests.post(
            "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=query_payload,
            timeout=120
        )

        if query_response.status_code != 200:
            return None

        result = query_response.json()
        if result.get("status") != "1":
            return None

        return result.get("responseBody", {})
    except Exception as e:
        if not silencioso:
            print(f"  [ERRO] {str(e)[:50]}")
        return None

def main():
    print("=" * 80)
    print("MAPEAMENTO COMPLETO DO BANCO SANKHYA")
    print("=" * 80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    access_token = autenticar()
    if not access_token:
        return

    mapeamento = {
        "data_extracao": datetime.now().isoformat(),
        "tabelas_por_prefixo": {},
        "tabelas_detalhes": {},
        "relacionamentos": [],
        "estatisticas": {}
    }

    # ========================================
    # FASE 1: LISTAR TODAS AS TABELAS
    # ========================================
    print("\n" + "=" * 80)
    print("FASE 1: LISTANDO TODAS AS TABELAS")
    print("=" * 80)

    # Prefixos conhecidos do Sankhya
    prefixos = [
        'TGF',   # Tabelas de Gestao Financeira/Comercial
        'TGW',   # Tabelas WMS
        'TSI',   # Tabelas de Sistema
        'TCS',   # Tabelas de Configuracao Sistema
        'TAI',   # Tabelas de AI/Integracao
        'TDI',   # Tabelas de DI
        'TCO',   # Tabelas de Controle
        'TCI',   # Tabelas CI
        'TAD',   # Tabelas Adicionais
        'TFP',   # Tabelas Fiscal/Producao
        'AD_',   # Tabelas Customizadas (AD_*)
        'VGW',   # Views WMS
        'VGF',   # Views Gestao
    ]

    query_tabelas = """
    SELECT
        TABLE_NAME,
        SUBSTR(TABLE_NAME, 1, 3) AS PREFIXO
    FROM ALL_TABLES
    WHERE OWNER = USER
    ORDER BY TABLE_NAME
    """

    result = executar_query(access_token, query_tabelas, "Listando todas as tabelas")

    if result and result.get("rows"):
        tabelas = result["rows"]
        print(f"\n[OK] Total de tabelas encontradas: {len(tabelas)}")

        # Agrupar por prefixo
        for row in tabelas:
            nome = row[0]
            # Determinar prefixo (3 ou 2 caracteres, ou AD_)
            if nome.startswith('AD_'):
                prefixo = 'AD_'
            elif nome.startswith('VGW'):
                prefixo = 'VGW'
            elif nome.startswith('VGF'):
                prefixo = 'VGF'
            else:
                prefixo = nome[:3] if len(nome) >= 3 else nome

            if prefixo not in mapeamento["tabelas_por_prefixo"]:
                mapeamento["tabelas_por_prefixo"][prefixo] = []
            mapeamento["tabelas_por_prefixo"][prefixo].append(nome)

        # Mostrar resumo por prefixo
        print("\nTabelas por prefixo:")
        print("-" * 40)
        for prefixo in sorted(mapeamento["tabelas_por_prefixo"].keys()):
            qtd = len(mapeamento["tabelas_por_prefixo"][prefixo])
            print(f"  {prefixo:<10}: {qtd:>5} tabelas")

        mapeamento["estatisticas"]["total_tabelas"] = len(tabelas)
        mapeamento["estatisticas"]["total_prefixos"] = len(mapeamento["tabelas_por_prefixo"])

    # ========================================
    # FASE 2: TABELAS PRINCIPAIS (TGF*, TGW*, TSI*)
    # ========================================
    print("\n" + "=" * 80)
    print("FASE 2: DETALHANDO TABELAS PRINCIPAIS")
    print("=" * 80)

    # Tabelas mais importantes para analise
    tabelas_principais = [
        # Comercial/Financeiro
        'TGFCAB', 'TGFITE', 'TGFPAR', 'TGFPRO', 'TGFVEN', 'TGFFIN',
        'TGFEST', 'TGFMOV', 'TGFRES', 'TGFTOP', 'TGFEMP', 'TGFNAT',
        # WMS
        'TGWEST', 'TGWEND', 'TGWREC', 'TGWSEP', 'TGWEMPE',
        # Cotacao
        'TGFCOT', 'TGFITC',
        # Sistema
        'TSIUSU', 'TSIEMP',
    ]

    print(f"\nAnalisando {len(tabelas_principais)} tabelas principais...")

    for tabela in tabelas_principais:
        print(f"\n  [{tabela}]")

        # Contar registros
        query_count = f"SELECT COUNT(*) FROM {tabela}"
        result_count = executar_query(access_token, query_count, f"Contando {tabela}", silencioso=True)

        qtd_registros = 0
        if result_count and result_count.get("rows"):
            qtd_registros = result_count["rows"][0][0] or 0

        # Obter colunas
        query_cols = f"""
        SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
        FROM ALL_TAB_COLUMNS
        WHERE TABLE_NAME = '{tabela}'
        ORDER BY COLUMN_ID
        """
        result_cols = executar_query(access_token, query_cols, f"Colunas de {tabela}", silencioso=True)

        colunas = []
        if result_cols and result_cols.get("rows"):
            for col in result_cols["rows"]:
                colunas.append({
                    "nome": col[0],
                    "tipo": col[1],
                    "tamanho": col[2],
                    "nullable": col[3]
                })

        mapeamento["tabelas_detalhes"][tabela] = {
            "registros": qtd_registros,
            "colunas": colunas,
            "qtd_colunas": len(colunas)
        }

        print(f"    Registros: {qtd_registros:,}")
        print(f"    Colunas: {len(colunas)}")

    # ========================================
    # FASE 3: RELACIONAMENTOS (CONSTRAINTS)
    # ========================================
    print("\n" + "=" * 80)
    print("FASE 3: MAPEANDO RELACIONAMENTOS")
    print("=" * 80)

    query_fk = """
    SELECT
        a.table_name AS TABELA_ORIGEM,
        a.column_name AS COLUNA_ORIGEM,
        c_pk.table_name AS TABELA_DESTINO,
        b.column_name AS COLUNA_DESTINO,
        a.constraint_name AS FK_NAME
    FROM all_cons_columns a
    JOIN all_constraints c ON a.constraint_name = c.constraint_name
    JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
    JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name
    WHERE c.constraint_type = 'R'
      AND a.owner = USER
    ORDER BY a.table_name, a.column_name
    FETCH FIRST 500 ROWS ONLY
    """

    result_fk = executar_query(access_token, query_fk, "Mapeando Foreign Keys")

    if result_fk and result_fk.get("rows"):
        print(f"\n[OK] Relacionamentos encontrados: {len(result_fk['rows'])}")

        for row in result_fk["rows"]:
            mapeamento["relacionamentos"].append({
                "tabela_origem": row[0],
                "coluna_origem": row[1],
                "tabela_destino": row[2],
                "coluna_destino": row[3],
                "fk_name": row[4]
            })

        # Mostrar alguns relacionamentos importantes
        print("\nRelacionamentos principais:")
        print("-" * 80)
        tabelas_foco = ['TGFCAB', 'TGFITE', 'TGWEMPE', 'TGFCOT', 'TGFITC']
        for rel in mapeamento["relacionamentos"]:
            if rel["tabela_origem"] in tabelas_foco or rel["tabela_destino"] in tabelas_foco:
                print(f"  {rel['tabela_origem']}.{rel['coluna_origem']} -> {rel['tabela_destino']}.{rel['coluna_destino']}")

    # ========================================
    # FASE 4: VIEWS IMPORTANTES
    # ========================================
    print("\n" + "=" * 80)
    print("FASE 4: LISTANDO VIEWS")
    print("=" * 80)

    query_views = """
    SELECT VIEW_NAME
    FROM ALL_VIEWS
    WHERE OWNER = USER
      AND (VIEW_NAME LIKE 'VGW%' OR VIEW_NAME LIKE 'VGF%' OR VIEW_NAME LIKE 'V_TGF%')
    ORDER BY VIEW_NAME
    FETCH FIRST 100 ROWS ONLY
    """

    result_views = executar_query(access_token, query_views, "Listando views")

    if result_views and result_views.get("rows"):
        views = [row[0] for row in result_views["rows"]]
        mapeamento["views"] = views
        print(f"\n[OK] Views encontradas: {len(views)}")
        for v in views[:20]:
            print(f"  - {v}")
        if len(views) > 20:
            print(f"  ... e mais {len(views) - 20} views")

    # ========================================
    # FASE 5: SALVAR RESULTADOS
    # ========================================
    print("\n" + "=" * 80)
    print("FASE 5: SALVANDO RESULTADOS")
    print("=" * 80)

    # Salvar JSON completo
    output_json = "mapeamento_banco_sankhya.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(mapeamento, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[OK] JSON salvo: {output_json}")

    # Estatisticas finais
    print("\n" + "=" * 80)
    print("ESTATISTICAS FINAIS")
    print("=" * 80)
    print(f"  Total de tabelas: {mapeamento['estatisticas'].get('total_tabelas', 0):,}")
    print(f"  Total de prefixos: {mapeamento['estatisticas'].get('total_prefixos', 0)}")
    print(f"  Tabelas detalhadas: {len(mapeamento['tabelas_detalhes'])}")
    print(f"  Relacionamentos: {len(mapeamento['relacionamentos'])}")
    print(f"  Views: {len(mapeamento.get('views', []))}")

    print("\n" + "=" * 80)
    print("MAPEAMENTO CONCLUIDO!")
    print("=" * 80)
    print(f"Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
