# -*- coding: utf-8 -*-
"""
Predictor de Demanda - Interface Simplificada

Wrapper para fazer predicoes rapidas sem precisar gerenciar o modelo.
Carrega modelos salvos automaticamente ou treina sob demanda.

Exemplo:
    predictor = DemandPredictor()
    resultado = predictor.forecast_product(codprod=12345, periods=30)
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

from ..config import SCIENTIST_CONFIG
from .demand_model import DemandForecastModel

logger = logging.getLogger(__name__)


class DemandPredictor:
    """
    Interface simplificada para previsao de demanda.

    Gerencia cache de modelos e treina automaticamente quando necessario.
    """

    def __init__(self, data_loader=None):
        """
        Inicializa o predictor.

        Args:
            data_loader: Loader de dados (opcional, usa AnalystDataLoader se nao especificado)
        """
        self._data_loader = data_loader
        self._models_cache: Dict[int, DemandForecastModel] = {}
        self._models_dir = SCIENTIST_CONFIG.get("models_dir") / "demand"

    @property
    def data_loader(self):
        """Retorna data loader, criando se necessario."""
        if self._data_loader is None:
            from ...analyst.data_loader import AnalystDataLoader
            self._data_loader = AnalystDataLoader()
        return self._data_loader

    def forecast_product(
        self,
        codprod: int,
        periods: int = 30,
        force_retrain: bool = False
    ) -> Dict[str, Any]:
        """
        Faz previsao para um produto especifico.

        ESTE E O METODO PRINCIPAL PARA O AGENTE LLM CHAMAR.

        Args:
            codprod: Codigo do produto
            periods: Dias para prever
            force_retrain: Forcar retreino do modelo

        Returns:
            Dict estruturado com previsao
        """
        # Verificar se tem modelo em cache
        if not force_retrain and codprod in self._models_cache:
            model = self._models_cache[codprod]
            return model.get_forecast_summary(periods)

        # Tentar carregar modelo salvo
        if not force_retrain:
            model = self._load_model(codprod)
            if model is not None:
                self._models_cache[codprod] = model
                return model.get_forecast_summary(periods)

        # Treinar novo modelo
        return self._train_and_forecast(codprod, periods)

    def forecast_multiple(
        self,
        codprods: List[int],
        periods: int = 30
    ) -> Dict[str, Any]:
        """
        Faz previsao para multiplos produtos.

        Args:
            codprods: Lista de codigos de produtos
            periods: Dias para prever

        Returns:
            Dict com previsoes de todos os produtos
        """
        results = {
            "produtos": {},
            "resumo": {
                "total_previsao": 0,
                "produtos_com_sucesso": 0,
                "produtos_com_erro": 0,
            }
        }

        for codprod in codprods:
            try:
                forecast = self.forecast_product(codprod, periods)

                if forecast.get("success"):
                    results["produtos"][codprod] = forecast
                    results["resumo"]["produtos_com_sucesso"] += 1
                    results["resumo"]["total_previsao"] += forecast.get("previsao", {}).get("total", 0)
                else:
                    results["produtos"][codprod] = {"error": forecast.get("error")}
                    results["resumo"]["produtos_com_erro"] += 1

            except Exception as e:
                results["produtos"][codprod] = {"error": str(e)}
                results["resumo"]["produtos_com_erro"] += 1

        return results

    def forecast_category(
        self,
        categoria: str,
        periods: int = 30,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Faz previsao agregada para uma categoria.

        Args:
            categoria: Nome ou codigo da categoria
            periods: Dias para prever
            top_n: Numero de produtos principais a prever

        Returns:
            Dict com previsao agregada
        """
        # Carregar dados de vendas
        df = self.data_loader.load("vendas")

        if df.empty:
            return {"success": False, "error": "Sem dados de vendas"}

        # Filtrar por categoria (se tiver coluna)
        # TODO: Implementar filtro por categoria quando tivermos mapeamento

        # Pegar top N produtos por volume
        top_products = (
            df.groupby("CODPROD")["QTDNEG"]
            .sum()
            .nlargest(top_n)
            .index.tolist()
        )

        # Fazer previsao para cada produto
        return self.forecast_multiple(top_products, periods)

    def _train_and_forecast(
        self,
        codprod: int,
        periods: int
    ) -> Dict[str, Any]:
        """Treina modelo e faz previsao."""
        # Carregar dados
        df = self.data_loader.load("vendas")

        if df.empty:
            return {
                "success": False,
                "error": "Sem dados de vendas disponiveis"
            }

        # Filtrar por produto
        df_produto = df[df["CODPROD"] == codprod]

        if len(df_produto) < 10:
            return {
                "success": False,
                "error": f"Dados insuficientes para produto {codprod} ({len(df_produto)} registros)"
            }

        # Criar e treinar modelo
        model = DemandForecastModel()
        train_result = model.fit(df_produto, codprod=codprod)

        if not train_result.get("success"):
            return train_result

        # Salvar modelo
        try:
            model.save()
        except Exception as e:
            logger.warning(f"Nao foi possivel salvar modelo: {e}")

        # Guardar em cache
        self._models_cache[codprod] = model

        # Fazer previsao
        return model.get_forecast_summary(periods)

    def _load_model(self, codprod: int) -> Optional[DemandForecastModel]:
        """Carrega modelo salvo do disco."""
        if not self._models_dir.exists():
            return None

        # Buscar modelo mais recente para o produto
        pattern = f"demand_model_{codprod}_*.pkl"
        models = list(self._models_dir.glob(pattern))

        if not models:
            return None

        # Pegar mais recente
        latest = max(models, key=lambda x: x.stat().st_mtime)

        try:
            return DemandForecastModel.load(str(latest))
        except Exception as e:
            logger.warning(f"Erro ao carregar modelo {latest}: {e}")
            return None

    def clear_cache(self, codprod: Optional[int] = None) -> None:
        """Limpa cache de modelos."""
        if codprod:
            self._models_cache.pop(codprod, None)
        else:
            self._models_cache.clear()

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Lista modelos salvos disponiveis."""
        if not self._models_dir.exists():
            return []

        models = []
        for model_file in self._models_dir.glob("*.pkl"):
            # Extrair info do nome
            name = model_file.stem
            parts = name.split("_")

            models.append({
                "file": model_file.name,
                "codprod": parts[2] if len(parts) > 2 else "unknown",
                "timestamp": parts[3] if len(parts) > 3 else "unknown",
                "size_kb": model_file.stat().st_size / 1024,
            })

        return models
