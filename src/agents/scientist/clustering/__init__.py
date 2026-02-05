# -*- coding: utf-8 -*-
"""
Modulo de Segmentacao (Clustering)

Usa K-Means para segmentar clientes e produtos.

Classes:
- CustomerSegmentation: Segmentacao RFM de clientes
- ProductSegmentation: Segmentacao de produtos por performance

Exemplo:
    from src.agents.scientist.clustering import CustomerSegmentation

    segmenter = CustomerSegmentation()
    segmenter.fit(df_vendas)
    resultado = segmenter.get_segmentation_summary()
"""

from .customers import CustomerSegmentation
from .products import ProductSegmentation

__all__ = [
    'CustomerSegmentation',
    'ProductSegmentation',
]
