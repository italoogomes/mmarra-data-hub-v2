# -*- coding: utf-8 -*-
"""
Teste da interface simplificada do Analista

Uso:
    python scripts/testes/testar_analista.py
"""

import sys
from pathlib import Path

# Adicionar raiz ao path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

print("=" * 60)
print("TESTE DO ANALISTA - Interface Simplificada")
print("=" * 60)
print()

# ============================================================================
# 1. IMPORT E INSTANCIACAO
# ============================================================================
print("[1] Importando e instanciando Analista...")

try:
    from src.agents.analyst import Analista, RECIPES

    analista = Analista(salvar_disco=True)

    print("    OK: Analista instanciado com sucesso")
    print(f"    Relatorios disponiveis: {analista.listar_relatorios()}")
    print(f"    Modulos KPIs: {analista.listar_modulos()}")
except Exception as e:
    print(f"    ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ============================================================================
# 2. DESCREVER RELATORIOS
# ============================================================================
print("[2] Descricao dos relatorios...")

for nome in ["vendas", "vendas_diario", "estoque_critico"]:
    info = analista.descrever_relatorio(nome)
    if info:
        print(f"    {nome}: {info['descricao']}")
        print(f"      KPIs: {len(info['kpis'])} metricas")
        print(f"      Periodo padrao: {info['periodo_padrao']}")

print()

# ============================================================================
# 3. CALCULAR KPIS DE VENDAS
# ============================================================================
print("[3] Calculando KPIs de vendas (ultimos 7 dias)...")

try:
    kpis = analista.kpis("vendas", periodo="7d")

    if "error" in kpis:
        print(f"    ERRO: {kpis['error']}")
    else:
        # Mostrar alguns KPIs
        if "faturamento_total" in kpis:
            fat = kpis["faturamento_total"]
            print(f"    Faturamento Total: {fat.get('formatted', fat.get('valor', 'N/A'))}")

        if "ticket_medio" in kpis:
            ticket = kpis["ticket_medio"]
            print(f"    Ticket Medio: {ticket.get('formatted', ticket.get('valor', 'N/A'))}")

        if "qtd_pedidos" in kpis:
            qtd = kpis["qtd_pedidos"]
            print(f"    Qtd Pedidos: {qtd.get('formatted', qtd.get('valor', 'N/A'))}")

        if "_metadata" in kpis:
            meta = kpis["_metadata"]
            print(f"    Registros analisados: {meta.get('registros', 'N/A')}")

except Exception as e:
    print(f"    ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# 4. GERAR RELATORIO DE VENDAS
# ============================================================================
print("[4] Gerando relatorio de vendas (HTML)...")

try:
    result = analista.relatorio("vendas", periodo="7d")

    print(f"    {result}")

    if result.success:
        print(f"    Arquivo: {result.caminho_arquivo}")
        print(f"    Registros: {result.registros_analisados:,}")

        # Perguntar se quer abrir
        print()
        resposta = input("    Deseja abrir o relatorio no navegador? (s/n): ")
        if resposta.lower() == "s":
            result.abrir()

except Exception as e:
    print(f"    ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# 5. GERAR RELATORIO COM FILTRO
# ============================================================================
print("[5] Testando relatorio com filtro de vendedor...")

try:
    # Primeiro, ver quais vendedores existem nos dados
    from src.agents.analyst import AnalystDataLoader

    loader = AnalystDataLoader()
    df = loader.load("vendas")

    if "CODVEND" in df.columns:
        top_vendedor = df["CODVEND"].value_counts().head(1)
        if len(top_vendedor) > 0:
            cod_vend = top_vendedor.index[0]
            print(f"    Filtrando por vendedor codigo {cod_vend}...")

            result = analista.relatorio("vendas", periodo="7d", vendedor=cod_vend)
            print(f"    {result}")
except Exception as e:
    print(f"    ERRO: {e}")

print()
print("=" * 60)
print("TESTE CONCLUIDO")
print("=" * 60)
