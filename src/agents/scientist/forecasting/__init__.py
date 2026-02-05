# -*- coding: utf-8 -*-
"""
Modulo de Previsao de Demanda

Usa Prophet para prever demanda futura de produtos.

Classes:
- DemandForecastModel: Modelo principal de previsao
- DemandPreprocessor: Preprocessamento dos dados
- DemandPredictor: Wrapper para predicoes rapidas

Exemplo:
    from src.agents.scientist.forecasting import DemandForecastModel

    model = DemandForecastModel()
    model.fit(df_vendas, codprod=12345)
    previsao = model.get_forecast_summary(periods=30)
"""

from .preprocessor import DemandPreprocessor
from .demand_model import DemandForecastModel
from .predictor import DemandPredictor

__all__ = [
    'DemandPreprocessor',
    'DemandForecastModel',
    'DemandPredictor',
]
