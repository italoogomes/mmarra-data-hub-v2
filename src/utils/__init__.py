# -*- coding: utf-8 -*-
"""
Utilitarios do Data Hub
"""

from .sankhya_client import SankhyaClient

# Azure e opcional - pode nao estar instalado
try:
    from .azure_storage import AzureDataLakeClient, criar_estrutura_datalake
    _AZURE_AVAILABLE = True
except ImportError:
    AzureDataLakeClient = None
    criar_estrutura_datalake = None
    _AZURE_AVAILABLE = False

__all__ = ['SankhyaClient', 'AzureDataLakeClient', 'criar_estrutura_datalake', '_AZURE_AVAILABLE']
