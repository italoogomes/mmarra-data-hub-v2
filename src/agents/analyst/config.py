# -*- coding: utf-8 -*-
"""
Configuracoes do Agente Analista

Centraliza configuracoes especificas do agente:
- KPIs habilitados por modulo
- Fontes de dados (Data Lake vs API)
- Configuracoes de cache e refresh
"""

from pathlib import Path

# Diretorio base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Configuracao geral do Agente Analista
ANALYST_CONFIG = {
    # Cache de dados em memoria (segundos)
    "cache_ttl": 300,  # 5 minutos

    # Formato padrao de datas
    "date_format": "%Y-%m-%d",

    # Locale para formatacao de moeda
    "locale": "pt_BR",

    # Diretorio de saida para relatorios
    "output_dir": BASE_DIR / "output" / "reports",

    # Templates de relatorio
    "templates_dir": Path(__file__).parent / "reports" / "templates",
}

# Configuracao de fontes de dados
DATA_SOURCES = {
    "datalake": {
        # Diretorio local dos dados Parquet
        "local_path": BASE_DIR / "src" / "data" / "raw",

        # Path no Azure Data Lake
        "remote_path": "raw/{entity}/",

        # Formato dos arquivos
        "format": "parquet",

        # Tentar carregar do local primeiro
        "prefer_local": True,
    },
    "sankhya": {
        # Usar API como fallback
        "use_api": True,

        # Timeout para queries (segundos)
        "timeout": 300,

        # Cache de resultados da API (segundos)
        "cache_ttl": 3600,  # 1 hora
    }
}

# Configuracao de KPIs por modulo
KPI_CONFIG = {
    "vendas": {
        "enabled": True,
        "frequency": "daily",
        "metrics": [
            "faturamento_total",
            "ticket_medio",
            "qtd_pedidos",
            "vendas_por_vendedor",
            "vendas_por_cliente",
            "taxa_desconto",
            "crescimento_mom",
            "top_produtos",
            "curva_abc_clientes",
        ],
        # Colunas necessarias do DataFrame
        "required_columns": [
            "NUNOTA", "VLRNOTA", "DTNEG", "CODVEND", "CODPARC"
        ],
        # Colunas opcionais
        "optional_columns": [
            "VLRDESCTOT", "VLRFRETE", "CODPROD", "QTDNEG"
        ],
    },
    "compras": {
        "enabled": True,
        "frequency": "daily",
        "metrics": [
            "volume_compras",
            "custo_medio_produto",
            "lead_time_fornecedor",
            "pedidos_pendentes",
            "taxa_conferencia_wms",
            "top_fornecedores",
            "economia_cotacao",
        ],
        "required_columns": [
            "NUNOTA", "VLRNOTA", "DTNEG", "CODPARC"
        ],
        "optional_columns": [
            "DTENTSAI", "VLRUNIT", "COD_SITUACAO"
        ],
    },
    "estoque": {
        "enabled": True,
        "frequency": "daily",
        "metrics": [
            "estoque_total_valor",
            "estoque_total_unidades",
            "giro_estoque",
            "produtos_sem_estoque",
            "cobertura_estoque",
            "divergencia_erp_wms",
            "taxa_ocupacao_wms",
            "produtos_parados",
            "curva_abc_estoque",
        ],
        "required_columns": [
            "CODPROD", "ESTOQUE", "DISPONIVEL"
        ],
        "optional_columns": [
            "RESERVADO", "VLRUNIT", "CODLOCAL", "CONTROLE"
        ],
    },
    "empenho": {
        "enabled": False,  # Fase futura
        "frequency": "daily",
        "metrics": [
            "taxa_empenho",
            "empenhos_pendentes",
            "tempo_medio_cotacao",
            "taxa_conversao_cotacao",
        ],
        "required_columns": [
            "NUNOTAPEDVEN", "CODPROD", "QTDEMPENHO"
        ],
        "optional_columns": [],
    },
}

# Mapeamento de entidades para tabelas Sankhya
ENTITY_TABLES = {
    "vendas": {
        "primary": "TGFCAB",
        "joins": ["TGFITE", "TGFPAR", "TGFVEN"],
        "filter": "TIPMOV = 'V'"
    },
    "compras": {
        "primary": "TGFCAB",
        "joins": ["TGFITE", "TGFPAR"],
        "filter": "TIPMOV = 'C'"
    },
    "estoque": {
        "primary": "TGFEST",
        "joins": ["TGFPRO", "TGFLOC"],
        "filter": None
    },
    "empenho": {
        "primary": "TGWEMPE",
        "joins": ["TGFCAB", "TGFITE"],
        "filter": None
    },
}

# Configuracoes de formatacao
FORMAT_CONFIG = {
    "currency": {
        "prefix": "R$ ",
        "decimal_sep": ",",
        "thousands_sep": ".",
        "decimals": 2,
    },
    "percentage": {
        "suffix": "%",
        "decimals": 1,
    },
    "number": {
        "decimal_sep": ",",
        "thousands_sep": ".",
        "decimals": 0,
    },
}
