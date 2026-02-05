# -*- coding: utf-8 -*-
"""
Loaders do Agente Engenheiro

Responsáveis por carregar dados nos destinos (Data Lake, DW, etc).
"""

from .datalake import DataLakeLoader

__all__ = ['DataLakeLoader']
