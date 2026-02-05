# -*- coding: utf-8 -*-
"""
Tools para o Agente LLM

Estas são as ferramentas que o LLM pode chamar para obter informações
dos outros agentes (Cientista, Analista, Engenheiro).
"""

from .forecast_tool import forecast_demand, ForecastTool
from .kpi_tool import get_kpis, KPITool
from .anomaly_tool import detect_anomalies, generate_anomaly_alerts

__all__ = [
    "forecast_demand",
    "ForecastTool",
    "get_kpis",
    "KPITool",
    "detect_anomalies",
    "generate_anomaly_alerts",
]
