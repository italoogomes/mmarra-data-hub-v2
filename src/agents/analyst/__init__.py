# -*- coding: utf-8 -*-
"""
Agente Analista - MMarra Data Hub

Gera KPIs, relatorios e dashboards a partir dos dados do Data Lake.
NAO usa LLM - apenas Python puro (pandas, jinja2, plotly).

Uso simplificado (RECOMENDADO):
    from src.agents.analyst import Analista

    analista = Analista()

    # Relatorio completo de vendas
    result = analista.relatorio("vendas")
    result.abrir()  # Abre no navegador

    # Relatorio com filtros
    result = analista.relatorio("vendas", cliente="CLIENTE X", periodo="30d")

    # Relatorios pre-definidos
    result = analista.relatorio("vendas_diario")
    result = analista.relatorio("estoque_critico")

    # Apenas KPIs (sem HTML)
    kpis = analista.kpis("vendas", periodo="30d")
    print(f"Faturamento: {kpis['faturamento_total']['formatted']}")

    # Listar relatorios disponiveis
    print(analista.listar_relatorios())

Uso avancado (componentes individuais):
    from src.agents.analyst import VendasKPI, ComprasKPI, EstoqueKPI
    from src.agents.analyst import ReportGenerator
    from src.agents.analyst import AnalystDataLoader

    # Carregar dados
    loader = AnalystDataLoader()
    df = loader.load("vendas", data_inicio="2026-01-01")

    # Calcular KPIs
    kpi = VendasKPI()
    resultado = kpi.calculate_all(df)

    # Gerar relatorio
    gen = ReportGenerator()
    html = gen.generate({"vendas": resultado})
"""

from .config import KPI_CONFIG, DATA_SOURCES, ANALYST_CONFIG
from .data_loader import AnalystDataLoader
from .kpis import VendasKPI, ComprasKPI, EstoqueKPI, BaseKPI
from .reports import ReportGenerator
from .dashboards import DashboardDataPrep
from .facade import Analista, ReportResult, ReportRecipe, RECIPES

__all__ = [
    # Interface simplificada (recomendada)
    'Analista',
    'ReportResult',
    'ReportRecipe',
    'RECIPES',
    # Configuracao
    'KPI_CONFIG',
    'DATA_SOURCES',
    'ANALYST_CONFIG',
    # Data Loader
    'AnalystDataLoader',
    # KPIs
    'BaseKPI',
    'VendasKPI',
    'ComprasKPI',
    'EstoqueKPI',
    # Reports
    'ReportGenerator',
    # Dashboards
    'DashboardDataPrep',
]
