# -*- coding: utf-8 -*-
"""
Configurações do Agente Engenheiro de Dados

Centraliza configurações específicas do agente.
"""

# Configurações de extração
EXTRACTION_CONFIG = {
    # Tamanho padrão das faixas para extração por range
    "default_range_size": 5000,

    # Timeout padrão para queries (segundos)
    "default_timeout": 300,

    # Número máximo de tentativas em caso de erro
    "max_retries": 3,

    # Intervalo entre tentativas (segundos)
    "retry_interval": 5
}

# Configurações de transformação
TRANSFORMATION_CONFIG = {
    # Aplicar limpeza de dados por padrão
    "clean_data": True,

    # Aplicar mapeamento de colunas por padrão
    "map_columns": False,

    # Remover duplicatas
    "remove_duplicates": True,

    # Preencher valores nulos
    "fill_nulls": True
}

# Configurações de carga
LOAD_CONFIG = {
    # Fazer upload para Azure por padrão
    "upload_to_cloud": True,

    # Sobrescrever arquivos existentes
    "overwrite": True,

    # Camada padrão
    "default_layer": "raw"
}

# Configurações de agendamento
SCHEDULE_CONFIG = {
    "vendedores": {
        "frequency": "weekly",
        "day": 0,  # Segunda-feira
        "hour": 6,
        "minute": 0
    },
    "clientes": {
        "frequency": "daily",
        "hour": 6,
        "minute": 0
    },
    "produtos": {
        "frequency": "daily",
        "hour": 6,
        "minute": 15
    },
    "estoque": {
        "frequency": "hourly",
        "minute": 0
    },
    "vendas": {
        "frequency": "daily",
        "hour": 6,
        "minute": 30
    },
    "compras": {
        "frequency": "daily",
        "hour": 6,
        "minute": 45
    },
    "pedidos_compra": {
        "frequency": "daily",
        "hour": 7,
        "minute": 0
    }
}

# Limites de extração por entidade (id_max)
ENTITY_LIMITS = {
    "clientes": {"id_column": "p.CODPARC", "id_max": 100000},
    "produtos": {"id_column": "p.CODPROD", "id_max": 600000},
    "estoque": {"id_column": "e.CODPROD", "id_max": 600000},
    "vendas": {"id_column": "c.NUNOTA", "id_max": 500000},
    "compras": {"id_column": "c.NUNOTA", "id_max": 500000},
    "pedidos_compra": {"id_column": "c.NUNOTA", "id_max": 500000}
}
