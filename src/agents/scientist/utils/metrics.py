# -*- coding: utf-8 -*-
"""
Metricas de Avaliacao de Modelos

Metricas disponiveis:
- MAPE: Mean Absolute Percentage Error
- MAE: Mean Absolute Error
- RMSE: Root Mean Squared Error
- R2: Coeficiente de Determinacao
"""

import logging
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calcula Mean Absolute Percentage Error (MAPE).

    Args:
        y_true: Valores reais
        y_pred: Valores previstos

    Returns:
        MAPE em porcentagem (0-100)
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # Evitar divisao por zero
    mask = y_true != 0
    if not mask.any():
        return 0.0

    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    return float(mape)


def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calcula Mean Absolute Error (MAE).

    Args:
        y_true: Valores reais
        y_pred: Valores previstos

    Returns:
        MAE
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mae = np.mean(np.abs(y_true - y_pred))
    return float(mae)


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calcula Root Mean Squared Error (RMSE).

    Args:
        y_true: Valores reais
        y_pred: Valores previstos

    Returns:
        RMSE
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    return float(rmse)


def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calcula Coeficiente de Determinacao (R2).

    Args:
        y_true: Valores reais
        y_pred: Valores previstos

    Returns:
        R2 (0-1, quanto maior melhor)
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        return 0.0

    r2 = 1 - (ss_res / ss_tot)
    return float(r2)


def evaluate_forecast(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Avalia previsao calculando multiplas metricas.

    Args:
        y_true: Valores reais
        y_pred: Valores previstos
        metrics: Lista de metricas a calcular (default: todas)

    Returns:
        Dict com metricas calculadas
    """
    if metrics is None:
        metrics = ["mape", "mae", "rmse", "r2"]

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    result = {
        "n_samples": len(y_true),
        "metrics": {},
    }

    metric_functions = {
        "mape": calculate_mape,
        "mae": calculate_mae,
        "rmse": calculate_rmse,
        "r2": calculate_r2,
    }

    for metric in metrics:
        metric_lower = metric.lower()
        if metric_lower in metric_functions:
            value = metric_functions[metric_lower](y_true, y_pred)
            result["metrics"][metric_lower] = round(value, 4)

    # Adicionar interpretacao
    result["interpretation"] = _interpret_metrics(result["metrics"])

    return result


def _interpret_metrics(metrics: Dict[str, float]) -> Dict[str, str]:
    """
    Interpreta as metricas calculadas.

    Returns:
        Dict com interpretacao de cada metrica
    """
    interpretation = {}

    # MAPE
    if "mape" in metrics:
        mape = metrics["mape"]
        if mape < 10:
            interpretation["mape"] = "Excelente (erro < 10%)"
        elif mape < 20:
            interpretation["mape"] = "Bom (erro 10-20%)"
        elif mape < 30:
            interpretation["mape"] = "Razoavel (erro 20-30%)"
        else:
            interpretation["mape"] = "Ruim (erro > 30%)"

    # R2
    if "r2" in metrics:
        r2 = metrics["r2"]
        if r2 > 0.9:
            interpretation["r2"] = "Excelente (R2 > 0.9)"
        elif r2 > 0.7:
            interpretation["r2"] = "Bom (R2 0.7-0.9)"
        elif r2 > 0.5:
            interpretation["r2"] = "Razoavel (R2 0.5-0.7)"
        else:
            interpretation["r2"] = "Ruim (R2 < 0.5)"

    return interpretation
