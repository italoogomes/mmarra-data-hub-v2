# -*- coding: utf-8 -*-
"""
Modulo de Deteccao de Anomalias

Usa Isolation Forest para detectar padroes anomalos em vendas, compras e estoque.

Classes:
- AnomalyDetector: Detecta anomalias
- AlertGenerator: Gera alertas baseados em anomalias

Exemplo:
    from src.agents.scientist.anomaly import AnomalyDetector

    detector = AnomalyDetector()
    detector.fit(df_vendas)
    resultado = detector.get_anomalies_summary()
"""

from .detector import AnomalyDetector
from .alerts import AlertGenerator

__all__ = [
    'AnomalyDetector',
    'AlertGenerator',
]
