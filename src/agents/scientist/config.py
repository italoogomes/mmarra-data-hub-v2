# -*- coding: utf-8 -*-
"""
Configuracoes do Agente Cientista

Centraliza configuracoes de ML:
- Previsao de demanda (Prophet)
- Deteccao de anomalias (Isolation Forest)
- Segmentacao (K-Means)
"""

from pathlib import Path

# Diretorio base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Configuracao geral do Agente Cientista
SCIENTIST_CONFIG = {
    # Diretorio para salvar modelos treinados
    "models_dir": Path(__file__).parent / "models",

    # Diretorio de dados
    "data_dir": BASE_DIR / "src" / "data" / "raw",

    # Formato de salvamento de modelos
    "model_format": "pkl",

    # Nivel de log
    "log_level": "INFO",
}

# =============================================================================
# CONFIGURACAO DE PREVISAO DE DEMANDA (Prophet)
# =============================================================================
FORECAST_CONFIG = {
    # Parametros do Prophet
    "prophet": {
        # Tipo de sazonalidade
        "yearly_seasonality": True,
        "weekly_seasonality": True,
        "daily_seasonality": False,

        # Modo de sazonalidade ('additive' ou 'multiplicative')
        "seasonality_mode": "multiplicative",

        # Forca da sazonalidade
        "seasonality_prior_scale": 10.0,

        # Forca dos changepoints (pontos de mudanca de tendencia)
        "changepoint_prior_scale": 0.05,

        # Intervalo de confianca (0.8 = 80%)
        "interval_width": 0.80,

        # Numero de changepoints
        "n_changepoints": 25,
    },

    # Preprocessamento
    "preprocessing": {
        # Minimo de dias de historico para treinar
        # NOTA: Em produção, use 30+ dias. Valor 7 é apenas para teste.
        "min_history_days": 7,

        # Maximo de dias de historico (para performance)
        "max_history_days": 730,  # 2 anos

        # Preencher dias sem venda com zero
        "fill_missing_days": True,

        # Remover outliers antes de treinar
        "remove_outliers": True,

        # Limite de outliers (z-score)
        "outlier_zscore_threshold": 3.0,
    },

    # Previsao
    "prediction": {
        # Periodos padrao para previsao (dias)
        "default_periods": 30,

        # Maximo de periodos
        "max_periods": 365,

        # Incluir feriados brasileiros
        "include_holidays": True,
    },

    # Metricas de avaliacao
    "evaluation": {
        # Metricas a calcular
        "metrics": ["mape", "mae", "rmse", "r2"],

        # Percentual para validacao (train/test split)
        "test_size": 0.2,
    },
}

# =============================================================================
# CONFIGURACAO DE DETECCAO DE ANOMALIAS (Isolation Forest)
# =============================================================================
ANOMALY_CONFIG = {
    # Parametros do Isolation Forest
    "isolation_forest": {
        # Taxa de contaminacao esperada (% de anomalias)
        "contamination": 0.05,  # 5%

        # Numero de estimadores (arvores)
        "n_estimators": 100,

        # Maximo de amostras por arvore
        "max_samples": "auto",

        # Seed para reproducibilidade
        "random_state": 42,
    },

    # Features para deteccao
    "features": {
        "vendas": [
            "valor_venda",
            "quantidade",
            "desconto_percentual",
            "hora_venda",
            "dia_semana",
        ],
        "compras": [
            "valor_compra",
            "quantidade",
            "lead_time",
            "variacao_preco",
        ],
        "estoque": [
            "giro",
            "cobertura_dias",
            "variacao_estoque",
        ],
    },

    # Alertas
    "alerts": {
        # Gerar alerta para anomalias
        "generate_alerts": True,

        # Severidade baseada no score
        "severity_thresholds": {
            "critical": -0.8,  # score < -0.8
            "high": -0.6,      # score < -0.6
            "medium": -0.4,    # score < -0.4
            "low": -0.2,       # score < -0.2
        },
    },
}

# =============================================================================
# CONFIGURACAO DE SEGMENTACAO (K-Means)
# =============================================================================
CLUSTERING_CONFIG = {
    # Parametros do K-Means
    "kmeans": {
        # Numero de clusters (pode ser definido automaticamente)
        "n_clusters": None,  # None = usar metodo do cotovelo

        # Range para busca automatica
        "n_clusters_range": (2, 10),

        # Numero de inicializacoes
        "n_init": 10,

        # Maximo de iteracoes
        "max_iter": 300,

        # Seed para reproducibilidade
        "random_state": 42,
    },

    # Segmentacao de clientes (RFM)
    "customers": {
        "features": {
            "recency": "dias desde ultima compra",
            "frequency": "numero de compras",
            "monetary": "valor total gasto",
        },
        "default_n_clusters": 4,  # A, B, C, D
        "labels": {
            0: "VIP",
            1: "Regular",
            2: "Esporadico",
            3: "Inativo",
        },
    },

    # Segmentacao de produtos
    "products": {
        "features": {
            "volume_vendas": "quantidade vendida",
            "margem": "margem de lucro",
            "giro": "velocidade de venda",
        },
        "default_n_clusters": 3,  # A, B, C
        "labels": {
            0: "Estrela",      # Alto volume, alta margem
            1: "Vaca Leiteira", # Alto volume, baixa margem
            2: "Abacaxi",      # Baixo volume
        },
    },

    # Preprocessamento
    "preprocessing": {
        # Normalizar features
        "normalize": True,

        # Metodo de normalizacao ('standard' ou 'minmax')
        "normalization_method": "standard",
    },
}

# =============================================================================
# FERIADOS BRASILEIROS
# =============================================================================
BRAZILIAN_HOLIDAYS = {
    "fixed": [
        {"month": 1, "day": 1, "name": "Ano Novo"},
        {"month": 4, "day": 21, "name": "Tiradentes"},
        {"month": 5, "day": 1, "name": "Dia do Trabalho"},
        {"month": 9, "day": 7, "name": "Independencia"},
        {"month": 10, "day": 12, "name": "Nossa Senhora Aparecida"},
        {"month": 11, "day": 2, "name": "Finados"},
        {"month": 11, "day": 15, "name": "Proclamacao da Republica"},
        {"month": 12, "day": 25, "name": "Natal"},
    ],
    # Feriados moveis sao calculados dinamicamente
    "include_carnival": True,
    "include_easter": True,
    "include_corpus_christi": True,
}
