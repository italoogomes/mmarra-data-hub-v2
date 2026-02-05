# -*- coding: utf-8 -*-
"""
Agente Cientista - MMarra Data Hub

Modelos de Machine Learning para analise preditiva e deteccao de padroes.
NAO usa LLM - usa bibliotecas de ML (Prophet, scikit-learn, numpy).

Modulos:
- forecasting/: Previsao de demanda (Prophet)
- anomaly/: Deteccao de anomalias (Isolation Forest)
- clustering/: Segmentacao de clientes/produtos (K-Means)

IMPORTANTE:
- Todos os metodos retornam DADOS ESTRUTURADOS (dict)
- O Agente LLM chama esses metodos via tools
- Quem explica pro usuario e o LLM, nao o Cientista

Exemplo de uso:
    from src.agents.scientist import DemandForecastModel

    model = DemandForecastModel()
    model.fit(df_vendas, codprod=12345)
    previsao = model.get_forecast_summary(periods=30)
    # -> Dict estruturado com previsao, tendencia, sazonalidade
"""

from .config import SCIENTIST_CONFIG, FORECAST_CONFIG, ANOMALY_CONFIG, CLUSTERING_CONFIG
from .forecasting import DemandForecastModel, DemandPreprocessor, DemandPredictor
from .anomaly import AnomalyDetector, AlertGenerator
from .clustering import CustomerSegmentation, ProductSegmentation

__all__ = [
    # Config
    'SCIENTIST_CONFIG',
    'FORECAST_CONFIG',
    'ANOMALY_CONFIG',
    'CLUSTERING_CONFIG',
    # Forecasting
    'DemandForecastModel',
    'DemandPreprocessor',
    'DemandPredictor',
    # Anomaly
    'AnomalyDetector',
    'AlertGenerator',
    # Clustering
    'CustomerSegmentation',
    'ProductSegmentation',
]
