# -*- coding: utf-8 -*-
"""
Modelo de Previsao de Demanda com Prophet

Classe principal para treinar e prever demanda de produtos.

IMPORTANTE:
- Retorna DADOS ESTRUTURADOS (dict), nao texto
- O Agente LLM chama get_forecast_summary() via tool
- Quem explica pro usuario e o LLM

Exemplo:
    model = DemandForecastModel()
    model.fit(df_vendas, codprod=12345)
    resultado = model.get_forecast_summary(periods=30)
    # -> {
    #     "previsao_total": 450,
    #     "tendencia": "alta",
    #     "sazonalidade": {...},
    #     ...
    # }
"""

import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet nao instalado. Instale com: pip install prophet")

from ..config import FORECAST_CONFIG, SCIENTIST_CONFIG
from ..utils.holidays import get_holidays_dataframe
from ..utils.metrics import evaluate_forecast
from .preprocessor import DemandPreprocessor

logger = logging.getLogger(__name__)


class DemandForecastModel:
    """
    Modelo de previsao de demanda usando Prophet.

    Metodos principais:
    - fit(): Treina o modelo
    - predict(): Gera previsoes
    - get_forecast_summary(): Retorna dict estruturado (para LLM)
    - save() / load(): Persistencia do modelo
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o modelo.

        Args:
            config: Configuracoes do Prophet (opcional)
        """
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet nao instalado. Instale com: pip install prophet")

        self.config = config or FORECAST_CONFIG.get("prophet", {})
        self.preprocessor = DemandPreprocessor()

        self.model: Optional[Prophet] = None
        self.df_train: Optional[pd.DataFrame] = None
        self.forecast: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}

    def fit(
        self,
        df: pd.DataFrame,
        codprod: Optional[int] = None,
        date_col: str = "DTNEG",
        value_col: str = "QTDNEG",
        include_holidays: bool = True
    ) -> Dict[str, Any]:
        """
        Treina o modelo com dados historicos.

        Args:
            df: DataFrame com dados de vendas
            codprod: Codigo do produto (opcional)
            date_col: Coluna de data
            value_col: Coluna de valor
            include_holidays: Incluir feriados brasileiros

        Returns:
            Dict com metadados do treinamento
        """
        # Preprocessar dados
        df_prophet, prep_metadata = self.preprocessor.prepare_for_prophet(
            df=df,
            date_col=date_col,
            value_col=value_col,
            codprod=codprod
        )

        # NOTA: Em produção, use min_days >= 30. Valor 5 é apenas para teste.
        min_days = 5
        if df_prophet.empty or len(df_prophet) < min_days:
            return {
                "success": False,
                "error": f"Dados insuficientes ({len(df_prophet)} < {min_days} dias)",
                "preprocessing": prep_metadata
            }

        # Guardar dados de treino
        self.df_train = df_prophet.copy()
        self.metadata = {
            "codprod": codprod,
            "trained_at": datetime.now().isoformat(),
            "preprocessing": prep_metadata,
        }

        # Criar modelo Prophet
        self.model = Prophet(
            yearly_seasonality=self.config.get("yearly_seasonality", True),
            weekly_seasonality=self.config.get("weekly_seasonality", True),
            daily_seasonality=self.config.get("daily_seasonality", False),
            seasonality_mode=self.config.get("seasonality_mode", "multiplicative"),
            seasonality_prior_scale=self.config.get("seasonality_prior_scale", 10.0),
            changepoint_prior_scale=self.config.get("changepoint_prior_scale", 0.05),
            interval_width=self.config.get("interval_width", 0.80),
            n_changepoints=self.config.get("n_changepoints", 25),
        )

        # Adicionar feriados
        if include_holidays:
            holidays = get_holidays_dataframe()
            self.model.add_country_holidays(country_name='BR')

        # Treinar
        logger.info(f"Treinando modelo com {len(df_prophet)} registros...")

        try:
            self.model.fit(df_prophet)
        except Exception as e:
            logger.error(f"Erro no treinamento: {e}")
            return {
                "success": False,
                "error": str(e),
                "preprocessing": prep_metadata
            }

        self.metadata["training_rows"] = len(df_prophet)
        self.metadata["success"] = True

        return {
            "success": True,
            "training_rows": len(df_prophet),
            "date_range": prep_metadata.get("date_range"),
            "codprod": codprod,
        }

    def predict(self, periods: int = 30) -> pd.DataFrame:
        """
        Gera previsoes para os proximos N periodos.

        Args:
            periods: Numero de dias para prever

        Returns:
            DataFrame com previsoes
        """
        if self.model is None:
            raise ValueError("Modelo nao treinado. Execute fit() primeiro.")

        max_periods = FORECAST_CONFIG.get("prediction", {}).get("max_periods", 365)
        periods = min(periods, max_periods)

        # Criar dataframe futuro
        future = self.model.make_future_dataframe(periods=periods)

        # Prever
        self.forecast = self.model.predict(future)

        return self.forecast

    def get_forecast_summary(
        self,
        periods: int = 30
    ) -> Dict[str, Any]:
        """
        Retorna resumo estruturado da previsao.

        ESTE E O METODO QUE O AGENTE LLM CHAMA VIA TOOL.

        Args:
            periods: Numero de dias para prever

        Returns:
            Dict estruturado com:
            - previsao_total: soma prevista
            - previsao_diaria: media diaria
            - tendencia: 'alta', 'baixa' ou 'estavel'
            - sazonalidade: padroes identificados
            - confianca: intervalo de confianca
            - metricas: MAPE, MAE se disponivel
        """
        if self.model is None:
            return {
                "success": False,
                "error": "Modelo nao treinado. Execute fit() primeiro."
            }

        # Gerar previsao se necessario
        if self.forecast is None:
            self.predict(periods)

        # Separar historico e futuro
        last_date = self.df_train["ds"].max()
        forecast_future = self.forecast[self.forecast["ds"] > last_date].copy()

        if forecast_future.empty:
            return {
                "success": False,
                "error": "Nenhuma previsao gerada para o futuro"
            }

        # Calcular metricas da previsao
        previsao_total = forecast_future["yhat"].sum()
        previsao_media = forecast_future["yhat"].mean()
        previsao_min = forecast_future["yhat_lower"].sum()
        previsao_max = forecast_future["yhat_upper"].sum()

        # Determinar tendencia
        tendencia = self._calculate_trend(forecast_future)

        # Sazonalidade semanal
        sazonalidade = self._analyze_seasonality()

        # Picos previstos
        picos = self._find_peaks(forecast_future)

        # Avaliar modelo (se tiver dados suficientes)
        evaluation = self._evaluate_model()

        return {
            "success": True,
            "codprod": self.metadata.get("codprod"),
            "periodo": {
                "inicio": str(forecast_future["ds"].min().date()),
                "fim": str(forecast_future["ds"].max().date()),
                "dias": len(forecast_future),
            },
            "previsao": {
                "total": round(float(previsao_total), 0),
                "media_diaria": round(float(previsao_media), 2),
                "intervalo_confianca": {
                    "minimo": round(float(previsao_min), 0),
                    "maximo": round(float(previsao_max), 0),
                    "nivel": f"{int(self.config.get('interval_width', 0.8) * 100)}%",
                },
            },
            "tendencia": tendencia,
            "sazonalidade": sazonalidade,
            "picos_previstos": picos,
            "avaliacao": evaluation,
            "metadata": {
                "trained_at": self.metadata.get("trained_at"),
                "training_rows": self.metadata.get("training_rows"),
            }
        }

    def _calculate_trend(self, forecast: pd.DataFrame) -> Dict[str, Any]:
        """Calcula tendencia da previsao."""
        if len(forecast) < 2:
            return {"direcao": "indefinida", "variacao_pct": 0}

        # Comparar primeira e ultima semana
        first_week = forecast.head(7)["yhat"].mean()
        last_week = forecast.tail(7)["yhat"].mean()

        if first_week == 0:
            variacao = 0
        else:
            variacao = ((last_week - first_week) / first_week) * 100

        if variacao > 5:
            direcao = "alta"
        elif variacao < -5:
            direcao = "baixa"
        else:
            direcao = "estavel"

        return {
            "direcao": direcao,
            "variacao_pct": round(float(variacao), 1),
            "primeira_semana_media": round(float(first_week), 2),
            "ultima_semana_media": round(float(last_week), 2),
        }

    def _analyze_seasonality(self) -> Dict[str, Any]:
        """Analisa padroes de sazonalidade."""
        result = {"semanal": None, "anual": None}

        if self.forecast is None or self.model is None:
            return result

        # Sazonalidade semanal
        if self.config.get("weekly_seasonality", True):
            try:
                weekly = self.forecast.groupby(
                    self.forecast["ds"].dt.day_name()
                )["weekly"].mean()

                # Ordenar por dia da semana
                days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                days_pt = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]

                weekly_sorted = []
                for i, day in enumerate(days_order):
                    if day in weekly.index:
                        weekly_sorted.append({
                            "dia": days_pt[i],
                            "efeito": round(float(weekly[day]), 3)
                        })

                # Encontrar melhor e pior dia
                if weekly_sorted:
                    melhor = max(weekly_sorted, key=lambda x: x["efeito"])
                    pior = min(weekly_sorted, key=lambda x: x["efeito"])

                    result["semanal"] = {
                        "por_dia": weekly_sorted,
                        "melhor_dia": melhor["dia"],
                        "pior_dia": pior["dia"],
                    }
            except Exception as e:
                logger.debug(f"Erro ao analisar sazonalidade semanal: {e}")

        return result

    def _find_peaks(self, forecast: pd.DataFrame, top_n: int = 5) -> List[Dict]:
        """Encontra picos previstos."""
        if forecast.empty:
            return []

        # Top N maiores valores
        top = forecast.nlargest(top_n, "yhat")

        peaks = []
        for _, row in top.iterrows():
            peaks.append({
                "data": str(row["ds"].date()),
                "dia_semana": row["ds"].strftime("%A"),
                "previsao": round(float(row["yhat"]), 2),
            })

        return peaks

    def _evaluate_model(self) -> Optional[Dict[str, Any]]:
        """Avalia o modelo usando validacao cruzada simples."""
        if self.df_train is None or len(self.df_train) < 30:
            return None

        try:
            # Usar ultimos 20% para validacao
            split_idx = int(len(self.df_train) * 0.8)
            train = self.df_train.iloc[:split_idx]
            test = self.df_train.iloc[split_idx:]

            # Treinar modelo temporario
            temp_model = Prophet(**{
                k: v for k, v in self.config.items()
                if k in ["yearly_seasonality", "weekly_seasonality", "seasonality_mode"]
            })
            temp_model.fit(train)

            # Prever
            future = temp_model.make_future_dataframe(periods=len(test))
            forecast = temp_model.predict(future)

            # Pegar apenas periodo de teste
            forecast_test = forecast.tail(len(test))

            # Calcular metricas
            y_true = test["y"].values
            y_pred = forecast_test["yhat"].values

            evaluation = evaluate_forecast(y_true, y_pred, ["mape", "mae", "r2"])

            return evaluation

        except Exception as e:
            logger.debug(f"Erro na avaliacao: {e}")
            return None

    def save(self, path: Optional[str] = None) -> str:
        """
        Salva modelo treinado.

        Args:
            path: Caminho para salvar (opcional)

        Returns:
            Caminho do arquivo salvo
        """
        if self.model is None:
            raise ValueError("Modelo nao treinado")

        if path is None:
            models_dir = SCIENTIST_CONFIG.get("models_dir") / "demand"
            models_dir.mkdir(parents=True, exist_ok=True)

            codprod = self.metadata.get("codprod", "geral")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = models_dir / f"demand_model_{codprod}_{timestamp}.pkl"

        # Salvar modelo e metadados
        data = {
            "model": self.model,
            "metadata": self.metadata,
            "config": self.config,
            "df_train": self.df_train,
        }

        with open(path, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Modelo salvo em: {path}")
        return str(path)

    @classmethod
    def load(cls, path: str) -> "DemandForecastModel":
        """
        Carrega modelo salvo.

        Args:
            path: Caminho do arquivo

        Returns:
            Instancia do modelo
        """
        with open(path, "rb") as f:
            data = pickle.load(f)

        instance = cls(config=data.get("config"))
        instance.model = data.get("model")
        instance.metadata = data.get("metadata", {})
        instance.df_train = data.get("df_train")

        return instance
