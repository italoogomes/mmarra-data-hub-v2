# -*- coding: utf-8 -*-
"""
Configuracoes centralizadas do Data Hub
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Diretorio raiz do projeto
ROOT_DIR = Path(__file__).parent.parent

# Carregar .env do mcp_sankhya
env_path = ROOT_DIR / 'mcp_sankhya' / '.env'
load_dotenv(env_path)

# Credenciais Sankhya
SANKHYA_CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
SANKHYA_CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
SANKHYA_X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

# URLs da API Sankhya
SANKHYA_AUTH_URL = "https://api.sankhya.com.br/authenticate"
SANKHYA_QUERY_URL = "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json"

# Diretorios de dados
DATA_DIR = ROOT_DIR / 'src' / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'

# Criar diretorios se nao existirem
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configuracoes de extracao
DEFAULT_BATCH_SIZE = 10000  # Registros por lote
DEFAULT_TIMEOUT = 120  # Segundos

# Azure Data Lake
AZURE_STORAGE_ACCOUNT = os.getenv('AZURE_STORAGE_ACCOUNT', '')
AZURE_STORAGE_KEY = os.getenv('AZURE_STORAGE_KEY', '')
AZURE_CONTAINER = os.getenv('AZURE_CONTAINER', 'datahub')
