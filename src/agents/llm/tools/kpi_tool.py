# -*- coding: utf-8 -*-
"""
Tool de KPIs

Permite ao LLM consultar KPIs de vendas, compras e estoque.
Chama internamente o Agente Analista.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_kpis(
    modulo: str = "vendas",
    periodo: str = "mes_atual"
) -> Dict[str, Any]:
    """
    Obtém KPIs de um módulo específico.

    Use esta ferramenta quando o usuário perguntar sobre:
    - Faturamento, margem, ticket médio
    - Indicadores de vendas, compras ou estoque
    - Métricas de performance
    - Relatórios gerenciais

    Args:
        modulo: Módulo de KPIs. Opções: "vendas", "compras", "estoque"
        periodo: Período para calcular. Opções: "mes_atual", "mes_anterior", "ano"

    Returns:
        Dict com os KPIs calculados
    """
    try:
        # Importar facade do analista
        from ...analyst import Analista

        analista = Analista()

        # Definir datas baseado no período
        hoje = datetime.now()

        if periodo == "mes_atual":
            data_inicio = hoje.replace(day=1)
            data_fim = hoje
        elif periodo == "mes_anterior":
            primeiro_dia_mes = hoje.replace(day=1)
            data_fim = primeiro_dia_mes - timedelta(days=1)
            data_inicio = data_fim.replace(day=1)
        elif periodo == "ano":
            data_inicio = hoje.replace(month=1, day=1)
            data_fim = hoje
        else:
            data_inicio = hoje.replace(day=1)
            data_fim = hoje

        # Calcular KPIs
        result = analista.kpis(
            modulo=modulo,
            data_inicio=data_inicio.strftime("%Y-%m-%d"),
            data_fim=data_fim.strftime("%Y-%m-%d")
        )

        if result:
            return {
                "success": True,
                "modulo": modulo,
                "periodo": {
                    "inicio": data_inicio.strftime("%Y-%m-%d"),
                    "fim": data_fim.strftime("%Y-%m-%d")
                },
                "kpis": result
            }
        else:
            return {
                "success": False,
                "error": f"Não foi possível calcular KPIs de {modulo}"
            }

    except ImportError:
        # Se o Analista não estiver implementado, retornar dados de exemplo
        logger.warning("Analista não disponível, retornando dados de exemplo")
        return {
            "success": True,
            "modulo": modulo,
            "periodo": periodo,
            "kpis": _get_sample_kpis(modulo),
            "nota": "Dados de exemplo - Analista não configurado"
        }
    except Exception as e:
        logger.error(f"Erro ao calcular KPIs: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def _get_sample_kpis(modulo: str) -> Dict[str, Any]:
    """Retorna KPIs de exemplo para demonstração."""

    if modulo == "vendas":
        return {
            "faturamento_total": 1500000.00,
            "quantidade_vendas": 850,
            "ticket_medio": 1764.71,
            "margem_media": 18.5,
            "top_produtos": [
                {"codigo": 261301, "nome": "MOLA PATIM FREIO", "qtd": 2532},
                {"codigo": 263340, "nome": "DIPS INDICADOR PORCA", "qtd": 2228},
            ]
        }
    elif modulo == "compras":
        return {
            "valor_total_compras": 980000.00,
            "quantidade_pedidos": 120,
            "lead_time_medio": 5.2,
            "top_fornecedores": [
                {"codigo": 101, "nome": "Fornecedor A", "valor": 250000},
                {"codigo": 102, "nome": "Fornecedor B", "valor": 180000},
            ]
        }
    elif modulo == "estoque":
        return {
            "valor_total_estoque": 2500000.00,
            "quantidade_skus": 15000,
            "giro_medio": 4.2,
            "cobertura_dias": 45,
            "produtos_zerados": 523
        }
    else:
        return {}


# Versão como classe
class KPITool:
    """Wrapper da tool de KPIs para uso como classe."""

    name = "get_kpis"
    description = """
    Obtém KPIs e métricas de vendas, compras ou estoque.
    Use quando o usuário perguntar sobre faturamento, margem, indicadores ou relatórios.
    """

    def __call__(
        self,
        modulo: str = "vendas",
        periodo: str = "mes_atual"
    ) -> Dict[str, Any]:
        return get_kpis(modulo, periodo)
