# -*- coding: utf-8 -*-
"""
Tool de Detecção de Anomalias para o Agente LLM.

Permite que o LLM detecte anomalias nos dados de vendas usando Isolation Forest.
"""

import logging
from typing import Dict, Any
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Diretório raiz
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent


@tool
def detect_anomalies(
    data_type: str = "vendas",
    top_n: int = 10,
    min_severity: str = "media"
) -> Dict[str, Any]:
    """
    Detecta anomalias nos dados de vendas ou estoque usando Isolation Forest.

    Use esta ferramenta quando o usuário perguntar sobre:
    - Vendas estranhas ou anormais
    - Valores fora do padrão
    - Transações suspeitas
    - Anomalias nos dados

    Args:
        data_type: Tipo de dados ('vendas' ou 'estoque')
        top_n: Número de anomalias para retornar (default: 10)
        min_severity: Severidade mínima ('baixa', 'media', 'alta', 'critica')

    Returns:
        Dict com resumo das anomalias encontradas:
        - total_anomalias: Quantidade total
        - taxa_anomalias: Percentual
        - por_severidade: Contagem por nível
        - top_anomalias: Lista das piores anomalias
    """
    try:
        import pandas as pd
        from src.agents.scientist.anomaly import AnomalyDetector

        # Determinar arquivo de dados
        if data_type == "vendas":
            data_path = ROOT_DIR / "src/data/raw/vendas/vendas.parquet"
            entity_type = "vendas"
        elif data_type == "estoque":
            data_path = ROOT_DIR / "src/data/raw/estoque/estoque.parquet"
            entity_type = "estoque"
        else:
            return {
                "success": False,
                "error": f"Tipo de dados '{data_type}' não suportado. Use 'vendas' ou 'estoque'."
            }

        # Verificar se arquivo existe
        if not data_path.exists():
            return {
                "success": False,
                "error": f"Dados não encontrados em: {data_path}. Execute a extração primeiro."
            }

        # Carregar dados
        logger.info(f"Carregando dados de: {data_path}")
        df = pd.read_parquet(data_path)

        if df.empty:
            return {
                "success": False,
                "error": "DataFrame vazio após carregamento."
            }

        # Criar e treinar detector
        logger.info(f"Treinando detector de anomalias ({entity_type})...")
        detector = AnomalyDetector()

        result = detector.fit(df, entity_type=entity_type)

        if not result.get("success"):
            return {
                "success": False,
                "error": f"Erro no treinamento: {result.get('error')}"
            }

        # Obter resumo
        resumo = detector.get_anomalies_summary(top_n=top_n)

        if not resumo.get("success"):
            return {
                "success": False,
                "error": f"Erro ao obter resumo: {resumo.get('error')}"
            }

        # Filtrar por severidade mínima se necessário
        severidade_ordem = ["baixa", "media", "alta", "critica"]
        min_idx = severidade_ordem.index(min_severity) if min_severity in severidade_ordem else 0

        # Filtrar top_anomalias
        anomalias_filtradas = [
            a for a in resumo.get("top_anomalias", [])
            if severidade_ordem.index(a.get("severidade", "baixa")) >= min_idx
        ]

        return {
            "success": True,
            "data_type": data_type,
            "total_registros": resumo.get("total_registros", 0),
            "total_anomalias": resumo.get("total_anomalias", 0),
            "taxa_anomalias": resumo.get("taxa_anomalias", 0),
            "por_severidade": resumo.get("por_severidade", {}),
            "top_anomalias": anomalias_filtradas[:top_n],
            "features_analisadas": resumo.get("features_analisadas", []),
            "filtro_severidade": min_severity
        }

    except ImportError as e:
        logger.error(f"Erro de importação: {e}")
        return {
            "success": False,
            "error": f"Dependência não encontrada: {e}"
        }
    except Exception as e:
        logger.error(f"Erro na detecção de anomalias: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def generate_anomaly_alerts(
    min_severity: str = "alta",
    format_type: str = "text"
) -> Dict[str, Any]:
    """
    Gera alertas formatados para anomalias detectadas.

    Use esta ferramenta quando o usuário pedir:
    - Alertas de anomalias
    - Notificações de problemas
    - Relatório de vendas suspeitas

    Args:
        min_severity: Severidade mínima ('baixa', 'media', 'alta', 'critica')
        format_type: Formato do alerta ('text', 'markdown', 'html')

    Returns:
        Dict com alertas formatados
    """
    try:
        import pandas as pd
        from src.agents.scientist.anomaly import AnomalyDetector, AlertGenerator

        # Carregar dados de vendas
        data_path = ROOT_DIR / "src/data/raw/vendas/vendas.parquet"

        if not data_path.exists():
            return {
                "success": False,
                "error": "Dados de vendas não encontrados."
            }

        df = pd.read_parquet(data_path)

        # Detectar anomalias
        detector = AnomalyDetector()
        result = detector.fit(df, entity_type="vendas")

        if not result.get("success"):
            return {
                "success": False,
                "error": f"Erro na detecção: {result.get('error')}"
            }

        # Obter resumo
        resumo = detector.get_anomalies_summary(top_n=20)

        # Gerar alertas
        alert_gen = AlertGenerator()
        alertas = alert_gen.generate_alerts(resumo, min_severity=min_severity)

        if alertas.get("total_alertas", 0) == 0:
            return {
                "success": True,
                "message": f"Nenhum alerta de severidade '{min_severity}' ou superior encontrado.",
                "total_alertas": 0
            }

        # Formatar
        mensagem = alert_gen.format_for_notification(alertas, format_type=format_type)

        return {
            "success": True,
            "total_alertas": alertas.get("total_alertas", 0),
            "resumo_severidade": alertas.get("resumo_severidade", {}),
            "mensagem_formatada": mensagem,
            "formato": format_type
        }

    except Exception as e:
        logger.error(f"Erro ao gerar alertas: {e}")
        return {
            "success": False,
            "error": str(e)
        }
