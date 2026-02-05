# -*- coding: utf-8 -*-
"""
Classe base para calculadores de KPI

Define a interface padrao que todos os calculadores devem implementar.
Garante que os KPIs retornem dados estruturados para o Agente LLM.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union

import pandas as pd

from ..config import FORMAT_CONFIG

logger = logging.getLogger(__name__)


class BaseKPI(ABC):
    """
    Classe base abstrata para calculadores de KPI.

    Cada calculador deve implementar:
    - get_name(): Nome do modulo de KPI (vendas, compras, estoque)
    - get_available_metrics(): Lista de metricas disponiveis
    - calculate_all(): Calcula todos os KPIs do modulo

    Exemplo de uso:
        class VendasKPI(BaseKPI):
            def get_name(self) -> str:
                return "vendas"

            def calculate_all(self, df, **kwargs) -> Dict[str, Any]:
                return {
                    "faturamento_total": self._calc_faturamento(df),
                    ...
                }

        kpi = VendasKPI()
        resultado = kpi.calculate_all(df_vendas)
    """

    def __init__(self):
        """Inicializa o calculador de KPI."""
        self._format_config = FORMAT_CONFIG

    @abstractmethod
    def get_name(self) -> str:
        """
        Retorna o nome do modulo de KPI.

        Returns:
            Nome do modulo (ex: 'vendas', 'compras', 'estoque')
        """
        pass

    @abstractmethod
    def get_available_metrics(self) -> List[str]:
        """
        Retorna lista de metricas disponiveis neste modulo.

        Returns:
            Lista de nomes de metricas
        """
        pass

    @abstractmethod
    def calculate_all(
        self,
        df: pd.DataFrame,
        data_inicio: Optional[Union[str, date]] = None,
        data_fim: Optional[Union[str, date]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calcula todos os KPIs do modulo.

        Args:
            df: DataFrame com os dados
            data_inicio: Data inicial do periodo
            data_fim: Data final do periodo
            **kwargs: Parametros adicionais

        Returns:
            Dict estruturado com todos os KPIs calculados
        """
        pass

    def calculate_single(
        self,
        metric_name: str,
        df: pd.DataFrame,
        **kwargs
    ) -> Any:
        """
        Calcula uma metrica especifica.

        Args:
            metric_name: Nome da metrica
            df: DataFrame com os dados
            **kwargs: Parametros adicionais

        Returns:
            Valor da metrica calculada
        """
        method_name = f"_calc_{metric_name}"

        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(df, **kwargs)

        logger.warning(f"[{self.get_name()}] Metrica nao encontrada: {metric_name}")
        return None

    def _get_metadata(
        self,
        df: pd.DataFrame,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera metadados do calculo.

        Returns:
            Dict com metadados (timestamp, registros, periodo)
        """
        return {
            "modulo": self.get_name(),
            "calculated_at": datetime.now().isoformat(),
            "records_analyzed": len(df),
            "periodo": {
                "inicio": data_inicio,
                "fim": data_fim
            }
        }

    def _format_currency(self, value: float) -> str:
        """Formata valor como moeda brasileira."""
        config = self._format_config["currency"]
        formatted = f"{value:,.{config['decimals']}f}"
        # Trocar separadores para padrao brasileiro
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{config['prefix']}{formatted}"

    def _format_percentage(self, value: float) -> str:
        """Formata valor como porcentagem."""
        config = self._format_config["percentage"]
        return f"{value:.{config['decimals']}f}{config['suffix']}"

    def _format_number(self, value: float) -> str:
        """Formata numero com separador de milhares."""
        config = self._format_config["number"]
        formatted = f"{value:,.{config['decimals']}f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted

    def _safe_divide(self, numerator: float, denominator: float) -> float:
        """Divisao segura (retorna 0 se denominador for 0)."""
        if denominator == 0:
            return 0.0
        return numerator / denominator

    def _validate_columns(
        self,
        df: pd.DataFrame,
        required: List[str],
        optional: List[str] = None
    ) -> Dict[str, bool]:
        """
        Valida se as colunas necessarias estao presentes.

        Returns:
            Dict indicando quais colunas estao presentes
        """
        result = {"valid": True, "missing": [], "present": []}

        for col in required:
            if col in df.columns:
                result["present"].append(col)
            else:
                result["missing"].append(col)
                result["valid"] = False

        if optional:
            result["optional_present"] = [c for c in optional if c in df.columns]

        if not result["valid"]:
            logger.warning(
                f"[{self.get_name()}] Colunas faltando: {result['missing']}"
            )

        return result

    def _build_response(
        self,
        df: pd.DataFrame,
        kpis: Dict[str, Any],
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Monta resposta padronizada com KPIs e metadados.

        Returns:
            Dict estruturado com KPIs e metadados
        """
        return {
            **kpis,
            "metadata": self._get_metadata(df, data_inicio, data_fim)
        }
