# Agente Cientista - MMarra Data Hub

**Status:** Operacional
**Versao:** 1.0.0
**Ultima Atualizacao:** 2026-02-04

---

## Visao Geral

O Agente Cientista implementa modelos de Machine Learning para analise preditiva e deteccao de padroes. Ele consome dados do Data Lake e retorna dados estruturados.

**IMPORTANTE:** O Agente Cientista NAO usa LLM. Ele usa bibliotecas de ML (Prophet, scikit-learn). O Agente LLM (futuro) chamara os metodos do Cientista via tools para obter previsoes e explicar os resultados.

---

## Arquitetura

```
src/agents/scientist/
├── __init__.py              # Exports principais
├── config.py                # Configuracoes de ML
│
├── forecasting/             # Previsao de demanda
│   ├── __init__.py
│   ├── preprocessor.py      # Preparacao de dados
│   ├── demand_model.py      # Modelo Prophet
│   └── predictor.py         # Interface simplificada
│
├── anomaly/                 # Deteccao de anomalias
│   ├── __init__.py
│   ├── detector.py          # Isolation Forest
│   └── alerts.py            # Gerador de alertas
│
├── clustering/              # Segmentacao
│   ├── __init__.py
│   ├── customers.py         # Segmentacao RFM
│   └── products.py          # Segmentacao de produtos
│
├── models/                  # Modelos treinados salvos
│   ├── demand/
│   ├── anomaly/
│   └── clustering/
│
└── utils/
    ├── __init__.py
    ├── holidays.py          # Feriados brasileiros
    └── metrics.py           # MAPE, MAE, RMSE, R2
```

---

## Modulos

### 1. Forecasting (Previsao de Demanda)

Usa **Prophet** para prever demanda futura de produtos.

```python
from src.agents.scientist import DemandForecastModel

# Treinar modelo
model = DemandForecastModel()
model.fit(df_vendas, codprod=12345)

# Obter previsao estruturada (para LLM)
resultado = model.get_forecast_summary(periods=30)
# -> {
#     "previsao": {"total": 450, "media_diaria": 15.0},
#     "tendencia": {"direcao": "alta", "variacao_pct": 12.5},
#     "sazonalidade": {"melhor_dia": "Sexta", "pior_dia": "Domingo"},
#     ...
# }
```

#### Interface Simplificada (Predictor)

```python
from src.agents.scientist import DemandPredictor

predictor = DemandPredictor()

# Previsao para um produto
resultado = predictor.forecast_product(codprod=12345, periods=30)

# Previsao para multiplos produtos
resultados = predictor.forecast_multiple([12345, 12346, 12347], periods=30)
```

### 2. Anomaly (Deteccao de Anomalias)

Usa **Isolation Forest** para detectar padroes anomalos.

```python
from src.agents.scientist import AnomalyDetector, AlertGenerator

# Detectar anomalias
detector = AnomalyDetector()
detector.fit(df_vendas, entity_type="vendas")

# Obter resumo estruturado (para LLM)
resultado = detector.get_anomalies_summary()
# -> {
#     "total_anomalias": 15,
#     "taxa_anomalias": 3.5,
#     "por_severidade": {"critica": 2, "alta": 5, "media": 8},
#     "top_anomalias": [...],
# }

# Gerar alertas
alert_gen = AlertGenerator()
alertas = alert_gen.generate_alerts(resultado, min_severity="media")
```

### 3. Clustering (Segmentacao)

Usa **K-Means** para segmentar clientes e produtos.

#### Segmentacao de Clientes (RFM)

```python
from src.agents.scientist import CustomerSegmentation

segmenter = CustomerSegmentation()
segmenter.fit(df_vendas)

# Obter segmentacao estruturada (para LLM)
resultado = segmenter.get_segmentation_summary()
# -> {
#     "segmentos": [
#         {"nome": "VIP", "quantidade_clientes": 120, "percentual_receita": 65.3},
#         {"nome": "Regular", "quantidade_clientes": 450, "percentual_receita": 28.5},
#         ...
#     ],
#     "insights": ["O segmento VIP representa 8% dos clientes mas 65% da receita"]
# }

# Consultar cliente especifico
segmento = segmenter.get_customer_segment(codparc=12345)
```

#### Segmentacao de Produtos

```python
from src.agents.scientist import ProductSegmentation

segmenter = ProductSegmentation()
segmenter.fit(df_vendas)

resultado = segmenter.get_segmentation_summary()
# -> {
#     "segmentos": [...],
#     "curva_abc": {
#         "classe_A": {"quantidade": 50, "percentual_receita": 80},
#         ...
#     }
# }
```

---

## Integracao com Agente LLM (Futuro)

O Agente LLM chamara o Cientista via tools:

```python
# src/agents/llm/tools/forecast_tool.py

def forecast_demand(codprod: int, periods: int = 30) -> dict:
    """
    Tool que o LLM chama para obter previsao de demanda.

    Quando o usuario perguntar:
    "Quanto vou vender de pastilha de freio mes que vem?"

    O LLM chama esta tool, recebe os dados, e explica pro usuario.
    """
    from ...scientist.forecasting import DemandPredictor

    predictor = DemandPredictor()
    return predictor.forecast_product(codprod, periods)


# Definicao para LangChain/OpenAI Functions
FORECAST_TOOL = {
    'name': 'forecast_demand',
    'description': 'Faz previsao de demanda. Use quando perguntarem sobre vendas futuras.',
    'parameters': {
        'type': 'object',
        'properties': {
            'codprod': {'type': 'integer', 'description': 'Codigo do produto'},
            'periods': {'type': 'integer', 'description': 'Dias para prever', 'default': 30}
        },
        'required': ['codprod']
    }
}
```

---

## Configuracoes

### config.py

```python
# Previsao de Demanda
FORECAST_CONFIG = {
    "prophet": {
        "yearly_seasonality": True,
        "weekly_seasonality": True,
        "seasonality_mode": "multiplicative",
        "interval_width": 0.80,
    },
    "preprocessing": {
        "min_history_days": 30,
        "max_history_days": 730,
        "fill_missing_days": True,
        "remove_outliers": True,
    },
}

# Deteccao de Anomalias
ANOMALY_CONFIG = {
    "isolation_forest": {
        "contamination": 0.05,  # 5% de anomalias esperadas
        "n_estimators": 100,
    },
}

# Segmentacao
CLUSTERING_CONFIG = {
    "customers": {
        "default_n_clusters": 4,
        "labels": {0: "VIP", 1: "Regular", 2: "Esporadico", 3: "Inativo"},
    },
    "products": {
        "default_n_clusters": 3,
        "labels": {0: "Estrela", 1: "Vaca Leiteira", 2: "Abacaxi"},
    },
}
```

---

## Dependencias

```python
# requirements.txt
prophet>=1.1.0
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.0.0
```

### Instalacao do Prophet

```bash
# Windows (pode precisar de compilador C++)
pip install prophet

# Linux
pip install prophet

# Se der erro de compilacao:
conda install -c conda-forge prophet
```

---

## Estrutura dos Retornos

Todos os metodos retornam dicts estruturados:

```python
{
    "success": True,
    "previsao": {
        "total": 450,
        "media_diaria": 15.0,
        "intervalo_confianca": {"minimo": 380, "maximo": 520, "nivel": "80%"}
    },
    "tendencia": {
        "direcao": "alta",  # 'alta', 'baixa', 'estavel'
        "variacao_pct": 12.5
    },
    "metadata": {
        "trained_at": "2026-02-04T10:30:00",
        "training_rows": 365
    }
}
```

Isso permite que:
1. O Agente LLM interprete os valores
2. A interface exiba os dados formatados
3. Alertas sejam gerados automaticamente

---

## Metricas de Avaliacao

```python
from src.agents.scientist.utils.metrics import evaluate_forecast

evaluation = evaluate_forecast(y_true, y_pred)
# -> {
#     "metrics": {
#         "mape": 12.5,    # Mean Absolute Percentage Error
#         "mae": 5.2,      # Mean Absolute Error
#         "rmse": 7.8,     # Root Mean Squared Error
#         "r2": 0.85       # R-squared
#     },
#     "interpretation": {
#         "mape": "Bom (erro 10-20%)",
#         "r2": "Bom (R2 0.7-0.9)"
#     }
# }
```

---

## Feriados Brasileiros

```python
from src.agents.scientist.utils.holidays import get_holidays_dataframe

# Obter feriados para Prophet
holidays = get_holidays_dataframe(years_back=2, years_forward=1)
# -> DataFrame com ['ds', 'holiday']
# Inclui: Ano Novo, Carnaval, Pascoa, Tiradentes, Corpus Christi, etc.
```

---

## Testes

### Com dados sinteticos

```bash
python scripts/testes/testar_cientista_sintetico.py
```

### Com dados reais

```bash
python scripts/testes/testar_agente_cientista.py
```

> **NOTA:** Dados reais requerem colunas de data validas (DTNEG, DTFATUR).

---

## Limitacoes Conhecidas

1. **Prophet nao instalado por padrao** - Requer instalacao manual
2. **Dados do Data Lake** - Colunas de data podem estar vazias (verificar extracao)
3. **K-Means no Windows** - Warning de memory leak com MKL (nao afeta funcionamento)
4. **Segmentacao de Clientes** - Requer coluna de data valida para calculo de Recency

---

## Proximos Passos

- [ ] Implementar cache de modelos treinados (.pkl)
- [ ] Adicionar scheduler para retreino automatico
- [ ] Implementar validacao cruzada para Prophet
- [ ] Adicionar mais algoritmos de clustering (DBSCAN, Hierarchical)
- [ ] Implementar monitoramento de drift nos modelos

---

## Changelog

### v1.0.0 (2026-02-04)
- Implementacao inicial
- Modulo forecasting com Prophet
- Modulo anomaly com Isolation Forest
- Modulo clustering com K-Means (clientes e produtos)
- Feriados brasileiros
- Metricas de avaliacao (MAPE, MAE, RMSE, R2)
