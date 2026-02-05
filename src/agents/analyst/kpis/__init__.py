# -*- coding: utf-8 -*-
"""
Calculadores de KPIs do Agente Analista

Modulos disponiveis:
- vendas: KPIs de faturamento, ticket medio, vendas por vendedor
- compras: KPIs de volume, lead time, conferencia WMS
- estoque: KPIs de giro, cobertura, divergencias

Todos os KPIs retornam dicts estruturados para consumo pelo Agente LLM.
"""

from .base import BaseKPI
from .vendas import VendasKPI
from .compras import ComprasKPI
from .estoque import EstoqueKPI

__all__ = [
    'BaseKPI',
    'VendasKPI',
    'ComprasKPI',
    'EstoqueKPI',
]
