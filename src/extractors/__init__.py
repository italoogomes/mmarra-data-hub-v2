# -*- coding: utf-8 -*-
"""
Alias para os extractors do Agente Engenheiro.

Este módulo redireciona para src.agents.engineer.extractors
para manter compatibilidade com scripts antigos.
"""

from src.agents.engineer.extractors import (
    BaseExtractor,
    ClientesExtractor,
    VendasExtractor,
    ProdutosExtractor,
    EstoqueExtractor,
    VendedoresExtractor,
    ComprasExtractor,
    PedidosCompraExtractor,
)

__all__ = [
    'BaseExtractor',
    'ClientesExtractor',
    'VendasExtractor',
    'ProdutosExtractor',
    'EstoqueExtractor',
    'VendedoresExtractor',
    'ComprasExtractor',
    'PedidosCompraExtractor',
]
