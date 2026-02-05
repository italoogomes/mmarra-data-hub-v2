# -*- coding: utf-8 -*-
"""
Extractors do Agente Engenheiro

Responsáveis por extrair dados do Sankhya ERP via API.
"""

from .base import BaseExtractor
from .clientes import ClientesExtractor
from .vendas import VendasExtractor
from .produtos import ProdutosExtractor
from .estoque import EstoqueExtractor
from .vendedores import VendedoresExtractor
from .compras import ComprasExtractor, PedidosCompraExtractor

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
