# -*- coding: utf-8 -*-
"""
Preprocessador de Dados para Previsao de Demanda

Prepara dados de vendas para o formato esperado pelo Prophet:
- Coluna 'ds': data
- Coluna 'y': valor a prever

Funcionalidades:
- Agregacao por dia/semana/mes
- Preenchimento de dias sem venda
- Remocao de outliers
- Normalizacao
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np

from ..config import FORECAST_CONFIG

logger = logging.getLogger(__name__)


class DemandPreprocessor:
    """
    Preprocessa dados de vendas para Prophet.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o preprocessador.

        Args:
            config: Configuracoes de preprocessamento (opcional)
        """
        self.config = config or FORECAST_CONFIG.get("preprocessing", {})

    def prepare_for_prophet(
        self,
        df: pd.DataFrame,
        date_col: str = "DTNEG",
        value_col: str = "QTDNEG",
        codprod: Optional[int] = None,
        agg_func: str = "sum",
        freq: str = "D"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Prepara dados para o Prophet.

        Args:
            df: DataFrame com dados de vendas
            date_col: Coluna de data
            value_col: Coluna de valor (quantidade ou valor)
            codprod: Codigo do produto (filtra se especificado)
            agg_func: Funcao de agregacao ('sum', 'mean', 'count')
            freq: Frequencia ('D'=diario, 'W'=semanal, 'M'=mensal)

        Returns:
            Tuple: (DataFrame pronto para Prophet, metadados)
        """
        df_copy = df.copy()
        metadata = {
            "original_rows": len(df_copy),
            "date_col": date_col,
            "value_col": value_col,
            "freq": freq,
        }

        # Filtrar por produto se especificado
        if codprod is not None:
            if "CODPROD" in df_copy.columns:
                df_copy = df_copy[df_copy["CODPROD"] == codprod]
                metadata["codprod"] = codprod
                metadata["filtered_rows"] = len(df_copy)

        if df_copy.empty:
            logger.warning("DataFrame vazio apos filtro")
            return pd.DataFrame(columns=["ds", "y"]), metadata

        # Converter data
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col])

        # Garantir que value_col e numerico
        df_copy[value_col] = pd.to_numeric(df_copy[value_col], errors='coerce').fillna(0)

        # Agregar por data
        df_agg = df_copy.groupby(df_copy[date_col].dt.date).agg({
            value_col: agg_func
        }).reset_index()

        df_agg.columns = ["ds", "y"]
        df_agg["ds"] = pd.to_datetime(df_agg["ds"])

        # Ordenar por data
        df_agg = df_agg.sort_values("ds").reset_index(drop=True)

        metadata["aggregated_rows"] = len(df_agg)
        metadata["date_range"] = {
            "start": str(df_agg["ds"].min().date()) if len(df_agg) > 0 else None,
            "end": str(df_agg["ds"].max().date()) if len(df_agg) > 0 else None,
        }

        # Preencher dias faltantes
        if self.config.get("fill_missing_days", True) and len(df_agg) > 0:
            df_agg = self._fill_missing_days(df_agg)
            metadata["filled_rows"] = len(df_agg)

        # Remover outliers
        if self.config.get("remove_outliers", False) and len(df_agg) > 0:
            df_agg, outliers_removed = self._remove_outliers(df_agg)
            metadata["outliers_removed"] = outliers_removed

        # Limitar historico
        max_days = self.config.get("max_history_days", 730)
        if len(df_agg) > max_days:
            df_agg = df_agg.tail(max_days)
            metadata["limited_to_days"] = max_days

        # Verificar minimo de historico
        min_days = self.config.get("min_history_days", 30)
        if len(df_agg) < min_days:
            logger.warning(f"Historico insuficiente: {len(df_agg)} dias (minimo: {min_days})")
            metadata["warning"] = f"Historico insuficiente ({len(df_agg)} < {min_days} dias)"

        metadata["final_rows"] = len(df_agg)

        return df_agg, metadata

    def _fill_missing_days(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preenche dias faltantes com zero."""
        if df.empty:
            return df

        date_range = pd.date_range(
            start=df["ds"].min(),
            end=df["ds"].max(),
            freq="D"
        )

        df_full = pd.DataFrame({"ds": date_range})
        df_merged = df_full.merge(df, on="ds", how="left")
        df_merged["y"] = df_merged["y"].fillna(0)

        return df_merged

    def _remove_outliers(
        self,
        df: pd.DataFrame,
        zscore_threshold: Optional[float] = None
    ) -> Tuple[pd.DataFrame, int]:
        """
        Remove outliers usando Z-score.

        Returns:
            Tuple: (DataFrame limpo, numero de outliers removidos)
        """
        if df.empty:
            return df, 0

        threshold = zscore_threshold or self.config.get("outlier_zscore_threshold", 3.0)

        mean = df["y"].mean()
        std = df["y"].std()

        if std == 0:
            return df, 0

        df["zscore"] = (df["y"] - mean) / std
        outliers = df["zscore"].abs() > threshold

        n_outliers = outliers.sum()

        # Substituir outliers pela mediana
        if n_outliers > 0:
            median = df["y"].median()
            df.loc[outliers, "y"] = median

        df = df.drop(columns=["zscore"])

        return df, int(n_outliers)

    def get_data_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Gera relatorio de qualidade dos dados.

        Returns:
            Dict com metricas de qualidade
        """
        if df.empty or "y" not in df.columns:
            return {"error": "DataFrame vazio ou sem coluna 'y'"}

        return {
            "n_rows": len(df),
            "date_range": {
                "start": str(df["ds"].min().date()) if "ds" in df.columns else None,
                "end": str(df["ds"].max().date()) if "ds" in df.columns else None,
            },
            "y_stats": {
                "mean": float(df["y"].mean()),
                "median": float(df["y"].median()),
                "std": float(df["y"].std()),
                "min": float(df["y"].min()),
                "max": float(df["y"].max()),
                "zeros": int((df["y"] == 0).sum()),
                "zeros_pct": float((df["y"] == 0).mean() * 100),
            },
            "missing_days": self._count_missing_days(df) if "ds" in df.columns else None,
        }

    def _count_missing_days(self, df: pd.DataFrame) -> int:
        """Conta dias faltantes no historico."""
        if df.empty:
            return 0

        expected_days = (df["ds"].max() - df["ds"].min()).days + 1
        actual_days = len(df)

        return expected_days - actual_days
