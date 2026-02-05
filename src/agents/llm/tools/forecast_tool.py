# -*- coding: utf-8 -*-
"""
Tool de Previsão de Demanda

Permite ao LLM consultar previsões de demanda para produtos.
Chama internamente o Agente Cientista (DemandForecastModel).
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Diretório de modelos
MODELS_DIR = Path(__file__).parent.parent.parent / "scientist" / "models" / "demand"


def _find_model_for_product(codprod: int) -> Optional[Path]:
    """Encontra o modelo mais recente para um produto."""
    if not MODELS_DIR.exists():
        return None

    # Buscar modelo do produto
    pattern = f"demand_model_{codprod}_*.pkl"
    models = list(MODELS_DIR.glob(pattern))

    if not models:
        return None

    # Retornar o mais recente (por nome, que inclui timestamp)
    return sorted(models)[-1]


@tool
def forecast_demand(codprod: int, periods: int = 30) -> Dict[str, Any]:
    """
    Faz previsão de demanda para um produto.

    Use esta ferramenta quando o usuário perguntar sobre:
    - Previsão de vendas de um produto
    - Quanto vai vender de algo
    - Demanda futura
    - Planejamento de estoque

    Args:
        codprod: Código do produto no Sankhya (número inteiro)
        periods: Número de dias para prever (padrão: 30)

    Returns:
        Dict com previsão total, média diária, tendência e picos previstos
    """
    try:
        # Tentar carregar modelo existente
        model_path = _find_model_for_product(codprod)

        if model_path:
            # Carregar modelo treinado
            from ...scientist.forecasting import DemandForecastModel
            model = DemandForecastModel.load(str(model_path))

            # Gerar previsão
            result = model.get_forecast_summary(periods=periods)

            if result.get("success"):
                return {
                    "success": True,
                    "codprod": codprod,
                    "modelo": "carregado",
                    "previsao": result["previsao"],
                    "tendencia": result["tendencia"],
                    "picos": result.get("picos_previstos", [])[:3],
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Erro desconhecido na previsão")
                }
        else:
            return {
                "success": False,
                "error": f"Não encontrei modelo treinado para o produto {codprod}. "
                         "Execute primeiro o script de treinamento: python scripts/treinar_modelos.py"
            }

    except Exception as e:
        logger.error(f"Erro ao fazer previsão para produto {codprod}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Versão como classe (para uso com LangChain)
class ForecastTool:
    """Wrapper da tool de previsão para uso como classe."""

    name = "forecast_demand"
    description = """
    Faz previsão de demanda para um produto específico.
    Use quando o usuário perguntar sobre vendas futuras, previsão, demanda ou estoque.
    """

    def __call__(self, codprod: int, periods: int = 30) -> Dict[str, Any]:
        return forecast_demand(codprod, periods)
