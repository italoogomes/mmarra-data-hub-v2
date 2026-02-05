# -*- coding: utf-8 -*-
"""
Tools para o Agente LLM

Estas são as ferramentas que o LLM pode chamar para obter informações
dos outros agentes (Cientista, Analista, Engenheiro).
"""

from .forecast_tool import forecast_demand, ForecastTool
from .kpi_tool import get_kpis, KPITool

__all__ = [
    "forecast_demand",
    "ForecastTool",
    "get_kpis",
    "KPITool",
]
