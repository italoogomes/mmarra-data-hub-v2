# -*- coding: utf-8 -*-
"""
Gerador de Alertas de Anomalias

Gera alertas estruturados baseados em anomalias detectadas.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd

from ..config import ANOMALY_CONFIG

logger = logging.getLogger(__name__)


class AlertGenerator:
    """
    Gera alertas baseados em anomalias detectadas.

    Tipos de alerta:
    - Critico: Score < -0.8
    - Alto: Score < -0.6
    - Medio: Score < -0.4
    - Baixo: Score < -0.2
    """

    def __init__(self):
        """Inicializa o gerador de alertas."""
        self.thresholds = ANOMALY_CONFIG.get("alerts", {}).get("severity_thresholds", {
            "critical": -0.8,
            "high": -0.6,
            "medium": -0.4,
            "low": -0.2,
        })

    def generate_alerts(
        self,
        anomalies_summary: Dict[str, Any],
        min_severity: str = "media"
    ) -> Dict[str, Any]:
        """
        Gera alertas a partir do resumo de anomalias.

        Args:
            anomalies_summary: Resultado de AnomalyDetector.get_anomalies_summary()
            min_severity: Severidade minima para gerar alerta

        Returns:
            Dict com alertas gerados
        """
        if not anomalies_summary.get("success"):
            return {
                "success": False,
                "error": anomalies_summary.get("error", "Resumo de anomalias invalido")
            }

        severity_order = ["critica", "alta", "media", "baixa"]
        min_idx = severity_order.index(min_severity) if min_severity in severity_order else 2

        alerts = []
        top_anomalias = anomalies_summary.get("top_anomalias", [])

        for anomalia in top_anomalias:
            severity = anomalia.get("severidade", "baixa")
            severity_idx = severity_order.index(severity) if severity in severity_order else 3

            if severity_idx <= min_idx:
                alert = self._create_alert(anomalia)
                alerts.append(alert)

        # Resumo
        por_severidade = anomalies_summary.get("por_severidade", {})

        return {
            "success": True,
            "total_alertas": len(alerts),
            "alertas": alerts,
            "resumo_severidade": {
                "critica": por_severidade.get("critica", 0),
                "alta": por_severidade.get("alta", 0),
                "media": por_severidade.get("media", 0),
                "baixa": por_severidade.get("baixa", 0),
            },
            "gerado_em": datetime.now().isoformat(),
            "filtro_severidade": min_severity,
        }

    def _create_alert(self, anomalia: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um alerta estruturado."""
        severity = anomalia.get("severidade", "baixa")

        # Montar titulo
        if "NUNOTA" in anomalia:
            titulo = f"Anomalia em Nota {anomalia['NUNOTA']}"
        elif "CODPROD" in anomalia:
            titulo = f"Anomalia em Produto {anomalia['CODPROD']}"
        else:
            titulo = "Anomalia Detectada"

        # Montar descricao
        descricao_parts = []
        for key, value in anomalia.items():
            if key not in ["score", "severidade", "_anomaly_score", "_is_anomaly"]:
                if isinstance(value, float):
                    descricao_parts.append(f"{key}: {value:.2f}")
                else:
                    descricao_parts.append(f"{key}: {value}")

        return {
            "titulo": titulo,
            "severidade": severity,
            "score": anomalia.get("score"),
            "detalhes": anomalia,
            "descricao": " | ".join(descricao_parts),
            "acao_sugerida": self._suggest_action(severity, anomalia),
        }

    def _suggest_action(
        self,
        severity: str,
        anomalia: Dict[str, Any]
    ) -> str:
        """Sugere acao baseada na severidade."""
        if severity == "critica":
            return "Verificar imediatamente. Possivel erro ou fraude."
        elif severity == "alta":
            return "Investigar com prioridade. Valor fora do padrao."
        elif severity == "media":
            return "Revisar quando possivel. Pode indicar oportunidade ou problema."
        else:
            return "Monitorar. Variacao dentro do esperado."

    def format_for_notification(
        self,
        alerts: Dict[str, Any],
        format_type: str = "text"
    ) -> str:
        """
        Formata alertas para notificacao.

        Args:
            alerts: Resultado de generate_alerts()
            format_type: 'text', 'html' ou 'markdown'

        Returns:
            Alertas formatados como string
        """
        if not alerts.get("success") or not alerts.get("alertas"):
            return "Nenhum alerta para reportar."

        if format_type == "markdown":
            return self._format_markdown(alerts)
        elif format_type == "html":
            return self._format_html(alerts)
        else:
            return self._format_text(alerts)

    def _format_text(self, alerts: Dict[str, Any]) -> str:
        """Formata como texto simples."""
        lines = [
            f"=== ALERTAS DE ANOMALIAS ===",
            f"Total: {alerts['total_alertas']} alertas",
            f"Gerado em: {alerts['gerado_em']}",
            "",
        ]

        for alert in alerts["alertas"]:
            lines.append(f"[{alert['severidade'].upper()}] {alert['titulo']}")
            lines.append(f"  Score: {alert['score']}")
            lines.append(f"  {alert['descricao']}")
            lines.append(f"  Acao: {alert['acao_sugerida']}")
            lines.append("")

        return "\n".join(lines)

    def _format_markdown(self, alerts: Dict[str, Any]) -> str:
        """Formata como Markdown."""
        lines = [
            "# Alertas de Anomalias",
            "",
            f"**Total:** {alerts['total_alertas']} alertas",
            f"**Gerado em:** {alerts['gerado_em']}",
            "",
            "## Alertas",
            "",
        ]

        for alert in alerts["alertas"]:
            emoji = {"critica": "🔴", "alta": "🟠", "media": "🟡", "baixa": "🟢"}.get(alert["severidade"], "⚪")
            lines.append(f"### {emoji} {alert['titulo']}")
            lines.append(f"- **Severidade:** {alert['severidade']}")
            lines.append(f"- **Score:** {alert['score']}")
            lines.append(f"- **Detalhes:** {alert['descricao']}")
            lines.append(f"- **Acao:** {alert['acao_sugerida']}")
            lines.append("")

        return "\n".join(lines)

    def _format_html(self, alerts: Dict[str, Any]) -> str:
        """Formata como HTML."""
        colors = {"critica": "#dc3545", "alta": "#fd7e14", "media": "#ffc107", "baixa": "#28a745"}

        html = f"""
        <div style="font-family: Arial, sans-serif;">
            <h2>Alertas de Anomalias</h2>
            <p><strong>Total:</strong> {alerts['total_alertas']} alertas</p>
            <p><strong>Gerado em:</strong> {alerts['gerado_em']}</p>
        """

        for alert in alerts["alertas"]:
            color = colors.get(alert["severidade"], "#6c757d")
            html += f"""
            <div style="border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background: #f8f9fa;">
                <h4 style="margin: 0; color: {color};">{alert['titulo']}</h4>
                <p><strong>Severidade:</strong> {alert['severidade']} | <strong>Score:</strong> {alert['score']}</p>
                <p>{alert['descricao']}</p>
                <p><em>Acao: {alert['acao_sugerida']}</em></p>
            </div>
            """

        html += "</div>"
        return html
