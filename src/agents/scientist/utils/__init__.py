# -*- coding: utf-8 -*-
"""
Utilitarios do Agente Cientista

- holidays: Feriados brasileiros para Prophet
- metrics: Metricas de avaliacao de modelos (MAPE, MAE, etc)
"""

from .holidays import BrazilianHolidays, get_holidays_dataframe
from .metrics import (
    calculate_mape,
    calculate_mae,
    calculate_rmse,
    calculate_r2,
    evaluate_forecast,
)

__all__ = [
    'BrazilianHolidays',
    'get_holidays_dataframe',
    'calculate_mape',
    'calculate_mae',
    'calculate_rmse',
    'calculate_r2',
    'evaluate_forecast',
]
