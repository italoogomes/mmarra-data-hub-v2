# -*- coding: utf-8 -*-
"""
Script de Teste - Agente Analista

Testa os KPIs com dados reais do Data Lake.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from datetime import datetime

print("=" * 60)
print("TESTE DO AGENTE ANALISTA - MMarra Data Hub")
print("=" * 60)
print()

# =============================================================================
# 1. Verificar dados disponíveis
# =============================================================================
print("[1] VERIFICANDO DADOS DISPONÍVEIS")
print("-" * 40)

data_dir = Path(__file__).parent.parent.parent / "src" / "data" / "raw"

entidades = ["vendas", "estoque", "clientes", "produtos", "vendedores"]

for entidade in entidades:
    entity_dir = data_dir / entidade
    if entity_dir.exists():
        arquivos = list(entity_dir.glob("*.parquet"))
        if arquivos:
            # Pegar o mais recente
            arquivo = max(arquivos, key=lambda x: x.stat().st_mtime)
            df = pd.read_parquet(arquivo)
            print(f"  {entidade:12}: {len(df):>8} registros | {len(df.columns)} colunas | {arquivo.name}")
        else:
            print(f"  {entidade:12}: sem arquivos Parquet")
    else:
        print(f"  {entidade:12}: pasta não existe")

print()

# =============================================================================
# 2. Testar KPIs de Vendas
# =============================================================================
print("[2] TESTANDO KPIs DE VENDAS")
print("-" * 40)

try:
    from src.agents.analyst.kpis.vendas import VendasKPI

    # Carregar dados de vendas
    vendas_dir = data_dir / "vendas"
    vendas_files = list(vendas_dir.glob("*.parquet"))

    if vendas_files:
        arquivo = max(vendas_files, key=lambda x: x.stat().st_mtime)
        df_vendas = pd.read_parquet(arquivo)

        print(f"  Arquivo: {arquivo.name}")
        print(f"  Registros: {len(df_vendas)}")
        print(f"  Colunas: {list(df_vendas.columns)}")
        print()

        # Calcular KPIs
        kpi = VendasKPI()
        resultado = kpi.calculate_all(df_vendas)

        print("  KPIs calculados:")

        if "faturamento_total" in resultado:
            print(f"    - Faturamento Total: {resultado['faturamento_total'].get('formatted', 'N/A')}")

        if "ticket_medio" in resultado:
            print(f"    - Ticket Médio: {resultado['ticket_medio'].get('formatted', 'N/A')}")

        if "qtd_pedidos" in resultado:
            print(f"    - Qtd Pedidos: {resultado['qtd_pedidos'].get('formatted', 'N/A')}")

        if "vendas_por_vendedor" in resultado:
            top_vend = resultado['vendas_por_vendedor'].get('total_vendedores', 0)
            print(f"    - Total Vendedores: {top_vend}")

        if "curva_abc_clientes" in resultado:
            abc = resultado['curva_abc_clientes']
            if 'classe_A' in abc:
                print(f"    - Curva ABC Classe A: {abc['classe_A'].get('qtd_clientes', 0)} clientes")

        if "error" in resultado:
            print(f"    ERRO: {resultado['error']}")
    else:
        print("  Sem dados de vendas disponíveis")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# 3. Testar KPIs de Estoque
# =============================================================================
print("[3] TESTANDO KPIs DE ESTOQUE")
print("-" * 40)

try:
    from src.agents.analyst.kpis.estoque import EstoqueKPI

    # Carregar dados de estoque
    estoque_dir = data_dir / "estoque"
    estoque_files = list(estoque_dir.glob("*.parquet"))

    if estoque_files:
        arquivo = max(estoque_files, key=lambda x: x.stat().st_mtime)
        df_estoque = pd.read_parquet(arquivo)

        print(f"  Arquivo: {arquivo.name}")
        print(f"  Registros: {len(df_estoque)}")
        print(f"  Colunas: {list(df_estoque.columns)}")
        print()

        # Calcular KPIs
        kpi = EstoqueKPI()
        resultado = kpi.calculate_all(df_estoque)

        print("  KPIs calculados:")

        if "estoque_total_unidades" in resultado:
            print(f"    - Estoque Total (un): {resultado['estoque_total_unidades'].get('formatted', 'N/A')}")

        if "produtos_com_estoque" in resultado:
            print(f"    - Produtos c/ Estoque: {resultado['produtos_com_estoque'].get('formatted', 'N/A')}")

        if "produtos_sem_estoque" in resultado:
            print(f"    - Produtos s/ Estoque: {resultado['produtos_sem_estoque'].get('formatted', 'N/A')}")

        if "estoque_reservado" in resultado:
            print(f"    - Estoque Reservado: {resultado['estoque_reservado'].get('formatted', 'N/A')}")

        if "estoque_disponivel" in resultado:
            print(f"    - Estoque Disponível: {resultado['estoque_disponivel'].get('formatted', 'N/A')}")

        if "error" in resultado:
            print(f"    ERRO: {resultado['error']}")
    else:
        print("  Sem dados de estoque disponíveis")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# 4. Testar Gerador de Relatório
# =============================================================================
print("[4] TESTANDO GERADOR DE RELATÓRIO")
print("-" * 40)

try:
    from src.agents.analyst.reports.generator import ReportGenerator

    # Coletar todos os KPIs
    kpis_coletados = {}

    # Vendas
    if 'df_vendas' in dir() and df_vendas is not None and not df_vendas.empty:
        kpi_vendas = VendasKPI()
        kpis_coletados['vendas'] = kpi_vendas.calculate_all(df_vendas)

    # Estoque
    if 'df_estoque' in dir() and df_estoque is not None and not df_estoque.empty:
        kpi_estoque = EstoqueKPI()
        kpis_coletados['estoque'] = kpi_estoque.calculate_all(df_estoque)

    if kpis_coletados:
        # Gerar relatório
        gen = ReportGenerator()

        output_path = Path(__file__).parent.parent.parent / "output" / "reports" / f"relatorio_teste_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = gen.generate(
            kpis=kpis_coletados,
            output_path=str(output_path),
            title="Relatório de Teste - Agente Analista"
        )

        print(f"  Relatório gerado: {output_path}")
        print(f"  Tamanho: {len(html)} caracteres")
    else:
        print("  Sem KPIs para gerar relatório")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# 5. Testar Data Loader com Fallback
# =============================================================================
print("[5] TESTANDO DATA LOADER")
print("-" * 40)

try:
    from src.agents.analyst.data_loader import AnalystDataLoader

    loader = AnalystDataLoader()

    # Listar entidades disponíveis
    print(f"  Entidades disponíveis: {loader.get_available_entities()}")

    # Tentar carregar vendas do Data Lake
    print("  Testando load('vendas') do Data Lake...")
    df_test = loader.load("vendas", force_source="datalake")

    if not df_test.empty:
        print(f"    OK - Carregado: {len(df_test)} registros")
    else:
        print(f"    AVISO - DataFrame vazio")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("TESTE CONCLUÍDO")
print("=" * 60)
