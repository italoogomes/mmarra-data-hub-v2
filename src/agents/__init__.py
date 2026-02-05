# -*- coding: utf-8 -*-
"""
Agentes do MMarra Data Hub

Agentes sao modulos Python permanentes que executam tarefas automatizadas:
- engineer: ETL (Extract, Transform, Load) - OPERACIONAL
- analyst: KPIs, relatorios, dashboards - OPERACIONAL
- scientist: ML, previsoes, anomalias - OPERACIONAL
- llm: Chat natural, SQL, RAG (futuro)

Exemplo de uso:
    # Agente Engenheiro
    from src.agents.engineer import Orchestrator
    orch = Orchestrator()
    orch.run_pipeline(["vendas", "estoque"])

    # Agente Analista
    from src.agents.analyst import VendasKPI, AnalystDataLoader
    loader = AnalystDataLoader()
    df = loader.load("vendas")
    kpi = VendasKPI()
    resultado = kpi.calculate_all(df)

    # Agente Cientista
    from src.agents.scientist import DemandForecastModel, AnomalyDetector
    model = DemandForecastModel()
    model.fit(df_vendas, codprod=12345)
    previsao = model.get_forecast_summary(periods=30)
"""

# Importar agentes disponiveis
from .engineer import Orchestrator, Scheduler
from .analyst import (
    VendasKPI,
    ComprasKPI,
    EstoqueKPI,
    AnalystDataLoader,
    ReportGenerator,
    DashboardDataPrep,
)

# Scientist - imports condicionais (dependem de prophet/sklearn)
try:
    from .scientist import (
        DemandForecastModel,
        DemandPredictor,
        AnomalyDetector,
        AlertGenerator,
        CustomerSegmentation,
        ProductSegmentation,
    )
    SCIENTIST_AVAILABLE = True
except ImportError:
    SCIENTIST_AVAILABLE = False

__all__ = [
    # Engineer
    'Orchestrator',
    'Scheduler',
    # Analyst
    'VendasKPI',
    'ComprasKPI',
    'EstoqueKPI',
    'AnalystDataLoader',
    'ReportGenerator',
    'DashboardDataPrep',
    # Scientist
    'DemandForecastModel',
    'DemandPredictor',
    'AnomalyDetector',
    'AlertGenerator',
    'CustomerSegmentation',
    'ProductSegmentation',
    'SCIENTIST_AVAILABLE',
]
