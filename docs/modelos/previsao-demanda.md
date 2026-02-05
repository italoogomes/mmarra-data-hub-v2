# 📊 Modelo de Previsão de Demanda - MMarra Data Hub

> Documentação técnica do modelo de ML para previsão de demanda em distribuidora automotiva.

---

## 🎯 Problema de Negócio

### Contexto: Distribuidora Automotiva

A MMarra trabalha com milhares de SKUs (peças automotivas) e precisa:

| Desafio | Impacto |
|---------|---------|
| **Estoque alto demais** | Capital parado, custo de armazenagem |
| **Estoque baixo demais** | Perda de venda, cliente vai pro concorrente |
| **Sazonalidade** | Algumas peças vendem mais em certas épocas |
| **Demanda irregular** | Peças de manutenção vs peças de colisão |

### Objetivo do Modelo

Responder perguntas como:
- "Quanto vou vender de pastilha de freio em março?"
- "Qual a previsão de demanda dessa peça pros próximos 30 dias?"
- "Quais produtos vão precisar de reposição na próxima semana?"

---

## 📈 Abordagem Técnica

### Por que Prophet?

| Biblioteca | Prós | Contras |
|------------|------|---------|
| **Prophet** ✅ | Fácil de usar, lida bem com sazonalidade, robusto a dados faltantes | Menos customizável |
| ARIMA | Clássico, bem documentado | Difícil de tunar, não lida bem com múltiplas sazonalidades |
| LSTM | Muito poderoso | Precisa de muitos dados, complexo |
| XGBoost | Muito flexível | Precisa de feature engineering manual |

**Prophet é ideal pra começar** porque:
- Funciona bem com dados diários/semanais
- Detecta sazonalidade automaticamente (semanal, mensal, anual)
- Lida com feriados brasileiros
- Fácil de interpretar os resultados

---

## 🗃️ Dados Necessários

### Do Sankhya (você já tem!)

```sql
-- Histórico de vendas por produto
SELECT
    TRUNC(CAB.DTNEG) AS DATA_VENDA,
    ITE.CODPROD,
    PRO.DESCRPROD,
    PRO.CODGRUPOPROD,          -- Grupo (filtros, freios, suspensão...)
    SUM(ITE.QTDNEG) AS QTD_VENDIDA,
    SUM(ITE.VLRTOT) AS VALOR_TOTAL,
    CAB.CODEMP                  -- Filial
FROM TGFCAB CAB
JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
JOIN TGFPRO PRO ON ITE.CODPROD = PRO.CODPROD
WHERE CAB.TIPMOV = 'V'         -- Vendas
  AND CAB.STATUSNOTA = 'L'     -- Liberadas
  AND CAB.DTNEG >= ADD_MONTHS(SYSDATE, -24)  -- Últimos 2 anos
GROUP BY TRUNC(CAB.DTNEG), ITE.CODPROD, PRO.DESCRPROD,
         PRO.CODGRUPOPROD, CAB.CODEMP
ORDER BY DATA_VENDA
```

### Estrutura do DataFrame

```python
# Formato esperado pelo Prophet
df_vendas = pd.DataFrame({
    'ds': ['2024-01-01', '2024-01-02', ...],  # Data
    'y': [150, 200, ...],                      # Quantidade vendida
    'codprod': [1001, 1001, ...],              # Código do produto
    'filial': [1, 1, ...]                      # Filial
})
```

### Dados Complementares (melhoram a previsão)

| Dado | Fonte | Impacto |
|------|-------|---------|
| Feriados nacionais/estaduais | Calendário | Alto |
| Dias úteis no mês | Calculado | Alto |
| Promoções passadas | Sankhya (TGFPROMO) | Médio |
| Clima (opcional) | API externa | Baixo |

---

## 🏗️ Arquitetura no Data Hub

### Onde fica no projeto

```
src/agents/scientist/
├── __init__.py
├── config.py
├── forecasting/
│   ├── __init__.py
│   ├── demand_model.py      # 🆕 Classe principal do modelo
│   ├── preprocessor.py      # 🆕 Prepara dados pro Prophet
│   ├── trainer.py           # 🆕 Treina e salva modelos
│   └── predictor.py         # 🆕 Faz previsões
├── models/                   # 🆕 Modelos treinados salvos
│   └── demand/
│       ├── produto_1001.pkl
│       ├── produto_1002.pkl
│       └── metadata.json
└── utils/
    ├── __init__.py
    ├── holidays.py          # 🆕 Feriados brasileiros
    └── metrics.py           # 🆕 MAPE, MAE, etc
```

### Fluxo de Dados

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Data Lake  │────►│ Preprocessor│────►│   Trainer   │
│  (vendas)   │     │             │     │  (Prophet)  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Agente LLM │◄────│  Predictor  │◄────│   Modelo    │
│  (explica)  │     │  (previsão) │     │   (.pkl)    │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 💻 Código do Modelo

### 1. Configuração (`config.py`)

```python
"""Configurações do Agente Cientista."""

from dataclasses import dataclass
from pathlib import Path

@dataclass
class ForecastConfig:
    """Configurações de previsão de demanda."""

    # Caminhos
    models_dir: Path = Path("src/agents/scientist/models/demand")

    # Prophet
    seasonality_mode: str = "multiplicative"  # Bom pra vendas
    yearly_seasonality: bool = True
    weekly_seasonality: bool = True
    daily_seasonality: bool = False  # Não precisamos diário

    # Previsão
    default_periods: int = 30  # Dias pra frente

    # Treinamento
    min_history_days: int = 90  # Mínimo de histórico
    retrain_frequency_days: int = 7  # Retreinar semanalmente

    # Métricas
    max_acceptable_mape: float = 0.25  # 25% de erro máximo aceitável
```

### 2. Feriados Brasileiros (`utils/holidays.py`)

```python
"""Feriados brasileiros para melhorar previsões."""

import pandas as pd
from datetime import date

def get_brazilian_holidays(start_year: int, end_year: int) -> pd.DataFrame:
    """
    Retorna DataFrame de feriados no formato do Prophet.

    Returns:
        DataFrame com colunas 'holiday', 'ds', 'lower_window', 'upper_window'
    """
    holidays = []

    for year in range(start_year, end_year + 1):
        # Feriados fixos
        fixed_holidays = [
            (f"{year}-01-01", "Ano Novo"),
            (f"{year}-04-21", "Tiradentes"),
            (f"{year}-05-01", "Dia do Trabalho"),
            (f"{year}-09-07", "Independência"),
            (f"{year}-10-12", "Nossa Senhora"),
            (f"{year}-11-02", "Finados"),
            (f"{year}-11-15", "Proclamação República"),
            (f"{year}-12-25", "Natal"),
        ]

        for ds, name in fixed_holidays:
            holidays.append({
                'holiday': name,
                'ds': pd.to_datetime(ds),
                'lower_window': -1,  # Dia antes também afeta
                'upper_window': 1,   # Dia depois também afeta
            })

        # TODO: Adicionar feriados móveis (Carnaval, Páscoa, Corpus Christi)
        # Usar biblioteca 'holidays' ou calcular manualmente

    return pd.DataFrame(holidays)


def get_automotive_events() -> pd.DataFrame:
    """
    Eventos específicos do setor automotivo que afetam demanda.

    Ex: Férias escolares (mais viagens = mais manutenção)
    """
    events = []

    # Período de férias (julho e dezembro/janeiro)
    # Aumenta demanda de peças de manutenção preventiva
    for year in range(2024, 2028):
        events.append({
            'holiday': 'Ferias_Julho',
            'ds': pd.to_datetime(f"{year}-07-01"),
            'lower_window': 0,
            'upper_window': 30,
        })
        events.append({
            'holiday': 'Ferias_FimAno',
            'ds': pd.to_datetime(f"{year}-12-15"),
            'lower_window': 0,
            'upper_window': 20,
        })

    return pd.DataFrame(events)
```

### 3. Preprocessador (`forecasting/preprocessor.py`)

```python
"""Prepara dados para o Prophet."""

import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DemandPreprocessor:
    """Preprocessa dados de vendas para previsão."""

    def __init__(self, min_history_days: int = 90):
        self.min_history_days = min_history_days

    def prepare_for_prophet(
        self,
        df: pd.DataFrame,
        date_col: str = 'data_venda',
        qty_col: str = 'qtd_vendida',
        product_col: str = 'codprod'
    ) -> dict[int, pd.DataFrame]:
        """
        Transforma dados de vendas no formato do Prophet.

        Args:
            df: DataFrame com histórico de vendas
            date_col: Nome da coluna de data
            qty_col: Nome da coluna de quantidade
            product_col: Nome da coluna de produto

        Returns:
            Dict {codprod: DataFrame pronto pro Prophet}
        """
        result = {}

        for codprod in df[product_col].unique():
            df_prod = df[df[product_col] == codprod].copy()

            # Verificar histórico mínimo
            if len(df_prod) < self.min_history_days:
                logger.warning(
                    f"Produto {codprod}: apenas {len(df_prod)} dias de histórico. "
                    f"Mínimo: {self.min_history_days}. Pulando."
                )
                continue

            # Formato Prophet: ds (data) e y (valor)
            df_prophet = pd.DataFrame({
                'ds': pd.to_datetime(df_prod[date_col]),
                'y': df_prod[qty_col].astype(float)
            })

            # Agregar por dia (caso tenha duplicatas)
            df_prophet = df_prophet.groupby('ds').agg({'y': 'sum'}).reset_index()

            # Preencher dias sem venda com 0
            df_prophet = self._fill_missing_dates(df_prophet)

            # Remover outliers extremos (opcional)
            df_prophet = self._remove_outliers(df_prophet)

            result[codprod] = df_prophet
            logger.info(f"Produto {codprod}: {len(df_prophet)} dias preparados")

        return result

    def _fill_missing_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preenche datas faltantes com 0."""
        date_range = pd.date_range(
            start=df['ds'].min(),
            end=df['ds'].max(),
            freq='D'
        )
        df_full = pd.DataFrame({'ds': date_range})
        df_full = df_full.merge(df, on='ds', how='left')
        df_full['y'] = df_full['y'].fillna(0)
        return df_full

    def _remove_outliers(
        self,
        df: pd.DataFrame,
        n_std: float = 3.0
    ) -> pd.DataFrame:
        """Remove outliers usando desvio padrão."""
        mean = df['y'].mean()
        std = df['y'].std()

        lower = mean - n_std * std
        upper = mean + n_std * std

        outliers = (df['y'] < lower) | (df['y'] > upper)
        n_outliers = outliers.sum()

        if n_outliers > 0:
            logger.info(f"Removendo {n_outliers} outliers")
            # Substitui por média móvel ao invés de remover
            df.loc[outliers, 'y'] = df['y'].rolling(7, center=True, min_periods=1).mean()

        return df
```

### 4. Modelo Principal (`forecasting/demand_model.py`)

```python
"""Modelo de previsão de demanda usando Prophet."""

import pandas as pd
import numpy as np
from prophet import Prophet
from pathlib import Path
import pickle
import json
import logging
from datetime import datetime
from typing import Optional

from ..config import ForecastConfig
from ..utils.holidays import get_brazilian_holidays, get_automotive_events
from .preprocessor import DemandPreprocessor

logger = logging.getLogger(__name__)


class DemandForecastModel:
    """
    Modelo de previsão de demanda para distribuidora automotiva.

    Usa Prophet para séries temporais com sazonalidade.
    """

    def __init__(self, config: Optional[ForecastConfig] = None):
        self.config = config or ForecastConfig()
        self.preprocessor = DemandPreprocessor(
            min_history_days=self.config.min_history_days
        )
        self.models: dict[int, Prophet] = {}
        self.metadata: dict = {}

        # Criar diretório de modelos
        self.config.models_dir.mkdir(parents=True, exist_ok=True)

    def train(
        self,
        df: pd.DataFrame,
        product_codes: Optional[list[int]] = None
    ) -> dict:
        """
        Treina modelos de previsão para produtos.

        Args:
            df: DataFrame com histórico de vendas
            product_codes: Lista de produtos para treinar (None = todos)

        Returns:
            Dict com métricas de treinamento
        """
        # Preparar dados
        data_by_product = self.preprocessor.prepare_for_prophet(df)

        if product_codes:
            data_by_product = {
                k: v for k, v in data_by_product.items()
                if k in product_codes
            }

        # Feriados
        holidays = pd.concat([
            get_brazilian_holidays(2023, 2027),
            get_automotive_events()
        ])

        results = {}

        for codprod, df_prophet in data_by_product.items():
            logger.info(f"Treinando modelo para produto {codprod}...")

            try:
                # Criar e configurar Prophet
                model = Prophet(
                    seasonality_mode=self.config.seasonality_mode,
                    yearly_seasonality=self.config.yearly_seasonality,
                    weekly_seasonality=self.config.weekly_seasonality,
                    daily_seasonality=self.config.daily_seasonality,
                    holidays=holidays,
                    interval_width=0.95,  # Intervalo de confiança 95%
                )

                # Treinar
                model.fit(df_prophet)

                # Salvar modelo
                self._save_model(model, codprod)
                self.models[codprod] = model

                # Calcular métricas (cross-validation simplificado)
                metrics = self._calculate_metrics(model, df_prophet)
                results[codprod] = metrics

                logger.info(
                    f"Produto {codprod}: MAPE={metrics['mape']:.2%}, "
                    f"MAE={metrics['mae']:.2f}"
                )

            except Exception as e:
                logger.error(f"Erro ao treinar produto {codprod}: {e}")
                results[codprod] = {'error': str(e)}

        # Salvar metadata
        self._save_metadata(results)

        return results

    def predict(
        self,
        codprod: int,
        periods: Optional[int] = None,
        include_history: bool = False
    ) -> pd.DataFrame:
        """
        Faz previsão para um produto.

        Args:
            codprod: Código do produto
            periods: Dias para prever (default: config.default_periods)
            include_history: Incluir dados históricos na resposta

        Returns:
            DataFrame com colunas: ds, yhat, yhat_lower, yhat_upper
        """
        periods = periods or self.config.default_periods

        # Carregar modelo se não estiver em memória
        if codprod not in self.models:
            self.models[codprod] = self._load_model(codprod)

        model = self.models[codprod]

        # Criar datas futuras
        future = model.make_future_dataframe(periods=periods)

        # Prever
        forecast = model.predict(future)

        # Selecionar colunas relevantes
        columns = ['ds', 'yhat', 'yhat_lower', 'yhat_upper']
        result = forecast[columns].copy()

        # Garantir valores não negativos (não faz sentido vender -5 peças)
        result['yhat'] = result['yhat'].clip(lower=0)
        result['yhat_lower'] = result['yhat_lower'].clip(lower=0)
        result['yhat_upper'] = result['yhat_upper'].clip(lower=0)

        if not include_history:
            # Retornar apenas futuro
            result = result.tail(periods)

        return result

    def predict_batch(
        self,
        product_codes: list[int],
        periods: Optional[int] = None
    ) -> dict[int, pd.DataFrame]:
        """Faz previsão para múltiplos produtos."""
        results = {}
        for codprod in product_codes:
            try:
                results[codprod] = self.predict(codprod, periods)
            except Exception as e:
                logger.error(f"Erro na previsão do produto {codprod}: {e}")
        return results

    def get_forecast_summary(
        self,
        codprod: int,
        periods: int = 30
    ) -> dict:
        """
        Retorna resumo da previsão para uso pelo Agente LLM.

        Returns:
            Dict com informações formatadas para o LLM interpretar
        """
        forecast = self.predict(codprod, periods)

        return {
            'codprod': codprod,
            'periodo_dias': periods,
            'previsao_total': round(forecast['yhat'].sum(), 0),
            'previsao_media_diaria': round(forecast['yhat'].mean(), 1),
            'intervalo_confianca': {
                'minimo': round(forecast['yhat_lower'].sum(), 0),
                'maximo': round(forecast['yhat_upper'].sum(), 0),
            },
            'tendencia': self._detect_trend(forecast),
            'dias_pico': self._get_peak_days(forecast),
            'data_geracao': datetime.now().isoformat(),
        }

    def _detect_trend(self, forecast: pd.DataFrame) -> str:
        """Detecta tendência (alta, baixa, estável)."""
        first_week = forecast.head(7)['yhat'].mean()
        last_week = forecast.tail(7)['yhat'].mean()

        change = (last_week - first_week) / first_week if first_week > 0 else 0

        if change > 0.1:
            return "alta"
        elif change < -0.1:
            return "baixa"
        else:
            return "estável"

    def _get_peak_days(self, forecast: pd.DataFrame, top_n: int = 3) -> list:
        """Retorna os dias com maior previsão."""
        top_days = forecast.nlargest(top_n, 'yhat')
        return [
            {
                'data': row['ds'].strftime('%Y-%m-%d'),
                'dia_semana': row['ds'].strftime('%A'),
                'previsao': round(row['yhat'], 0)
            }
            for _, row in top_days.iterrows()
        ]

    def _calculate_metrics(
        self,
        model: Prophet,
        df: pd.DataFrame
    ) -> dict:
        """Calcula métricas de performance."""
        # Previsão nos dados de treino (simplificado)
        forecast = model.predict(df)

        y_true = df['y'].values
        y_pred = forecast['yhat'].values

        # MAE - Mean Absolute Error
        mae = np.mean(np.abs(y_true - y_pred))

        # MAPE - Mean Absolute Percentage Error
        # Evitar divisão por zero
        mask = y_true != 0
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]))

        return {
            'mae': float(mae),
            'mape': float(mape),
            'n_samples': len(df),
            'trained_at': datetime.now().isoformat(),
        }

    def _save_model(self, model: Prophet, codprod: int):
        """Salva modelo treinado."""
        path = self.config.models_dir / f"produto_{codprod}.pkl"
        with open(path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Modelo salvo: {path}")

    def _load_model(self, codprod: int) -> Prophet:
        """Carrega modelo treinado."""
        path = self.config.models_dir / f"produto_{codprod}.pkl"
        if not path.exists():
            raise FileNotFoundError(f"Modelo não encontrado para produto {codprod}")

        with open(path, 'rb') as f:
            return pickle.load(f)

    def _save_metadata(self, results: dict):
        """Salva metadata dos treinamentos."""
        path = self.config.models_dir / "metadata.json"

        metadata = {
            'last_training': datetime.now().isoformat(),
            'n_models': len(results),
            'results': {str(k): v for k, v in results.items()},
        }

        with open(path, 'w') as f:
            json.dump(metadata, f, indent=2)
```

### 5. Integração com Agente LLM (`llm/tools/forecast_tool.py`)

```python
"""Ferramenta de previsão para o Agente LLM."""

from typing import Optional
import logging

from ...scientist.forecasting.demand_model import DemandForecastModel

logger = logging.getLogger(__name__)

# Instância global do modelo (carregada uma vez)
_forecast_model: Optional[DemandForecastModel] = None


def get_forecast_model() -> DemandForecastModel:
    """Retorna instância do modelo (singleton)."""
    global _forecast_model
    if _forecast_model is None:
        _forecast_model = DemandForecastModel()
    return _forecast_model


def forecast_demand(
    codprod: int,
    periods: int = 30,
    include_details: bool = True
) -> dict:
    """
    Ferramenta para o LLM consultar previsão de demanda.

    Args:
        codprod: Código do produto
        periods: Dias para prever
        include_details: Incluir detalhes da previsão

    Returns:
        Dict formatado para o LLM interpretar

    Exemplo de uso pelo LLM:
        User: "Quanto vou vender de pastilha de freio no próximo mês?"
        LLM: [chama forecast_demand(codprod=1001, periods=30)]
        LLM: "Baseado no histórico, a previsão é de vender aproximadamente
              450 unidades nos próximos 30 dias, com tendência estável..."
    """
    try:
        model = get_forecast_model()
        summary = model.get_forecast_summary(codprod, periods)

        if include_details:
            forecast_df = model.predict(codprod, periods)
            summary['previsao_diaria'] = [
                {
                    'data': row['ds'].strftime('%Y-%m-%d'),
                    'quantidade': round(row['yhat'], 0)
                }
                for _, row in forecast_df.iterrows()
            ]

        return {
            'success': True,
            'data': summary
        }

    except FileNotFoundError:
        return {
            'success': False,
            'error': f'Modelo não encontrado para produto {codprod}. '
                     'O produto pode não ter histórico suficiente.'
        }
    except Exception as e:
        logger.error(f"Erro na previsão: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# Definição da ferramenta para frameworks como LangChain
FORECAST_TOOL_DEFINITION = {
    'name': 'forecast_demand',
    'description': '''
        Faz previsão de demanda para um produto específico.
        Use quando o usuário perguntar sobre:
        - Previsão de vendas
        - Quanto vai vender de um produto
        - Demanda futura
        - Planejamento de estoque
    ''',
    'parameters': {
        'type': 'object',
        'properties': {
            'codprod': {
                'type': 'integer',
                'description': 'Código do produto no Sankhya'
            },
            'periods': {
                'type': 'integer',
                'description': 'Número de dias para prever (default: 30)',
                'default': 30
            }
        },
        'required': ['codprod']
    }
}
```

---

## 🚀 Como Usar

### 1. Treinar o Modelo

```python
from src.agents.scientist.forecasting.demand_model import DemandForecastModel
import pandas as pd

# Carregar dados do Data Lake
df_vendas = pd.read_parquet("data/raw/vendas/vendas.parquet")

# Criar e treinar modelo
model = DemandForecastModel()
results = model.train(df_vendas)

print(f"Modelos treinados: {len(results)}")
```

### 2. Fazer Previsão

```python
# Previsão para um produto específico
forecast = model.predict(codprod=1001, periods=30)
print(forecast)

# Resumo formatado (para o LLM)
summary = model.get_forecast_summary(codprod=1001, periods=30)
print(f"Previsão total: {summary['previsao_total']} unidades")
print(f"Tendência: {summary['tendencia']}")
```

### 3. Via Agente LLM

```
Usuário: "Quanto vou vender de pastilha de freio mês que vem?"

LLM internamente:
1. Identifica que precisa de previsão
2. Busca código do produto "pastilha de freio" → 1001
3. Chama forecast_demand(codprod=1001, periods=30)
4. Recebe: {previsao_total: 450, tendencia: "alta", ...}
5. Responde: "Baseado no histórico dos últimos 2 anos, a previsão
   é de vender aproximadamente 450 unidades de pastilha de freio
   no próximo mês, com tendência de alta de 12%. Os dias de maior
   demanda são tipicamente às sextas-feiras."
```

---

## 📊 Métricas de Avaliação

| Métrica | O que mede | Meta |
|---------|------------|------|
| **MAPE** | Erro percentual médio | < 25% |
| **MAE** | Erro absoluto médio | Depende do produto |
| **Cobertura** | % de valores reais dentro do intervalo | > 90% |

### Como interpretar

- **MAPE < 15%**: Excelente, modelo muito preciso
- **MAPE 15-25%**: Bom, aceitável para planejamento
- **MAPE 25-35%**: Regular, usar com cautela
- **MAPE > 35%**: Ruim, investigar o produto

---

## 🔧 Melhorias Futuras

1. **Cross-validation** mais robusto
2. **Regressores externos** (promoções, preço)
3. **Ensemble** de modelos (Prophet + XGBoost)
4. **Agrupamento** de produtos similares
5. **Retreinamento automático** semanal
6. **Alertas** quando previsão diverge muito do real

---

## 📦 Dependências

```txt
# Adicionar ao requirements.txt
prophet>=1.1.5
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0  # Para métricas
```

---

**Criado em:** 2026-02-03
**Versão:** 1.0
**Autor:** Documentação para MMarra Data Hub
