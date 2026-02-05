# -*- coding: utf-8 -*-
"""
Gerador de Relatorios HTML

Gera relatorios HTML a partir de KPIs calculados usando templates Jinja2.

Exemplo de uso:
    from src.agents.analyst.reports import ReportGenerator
    from src.agents.analyst.kpis import VendasKPI

    kpi = VendasKPI()
    resultado = kpi.calculate_all(df_vendas)

    gen = ReportGenerator()
    html = gen.generate(
        kpis={"vendas": resultado},
        template="daily.html",
        output_path="output/relatorio.html"
    )
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import ANALYST_CONFIG

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Gera relatorios HTML a partir de KPIs.

    Usa templates Jinja2 para renderizacao.
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Inicializa o gerador de relatorios.

        Args:
            template_dir: Diretorio com templates Jinja2
        """
        if template_dir is None:
            template_dir = ANALYST_CONFIG.get("templates_dir")

        self.template_dir = Path(template_dir) if template_dir else None
        self._env = None

    @property
    def env(self) -> Environment:
        """Retorna ambiente Jinja2, criando se necessario."""
        if self._env is None:
            if self.template_dir and self.template_dir.exists():
                loader = FileSystemLoader(str(self.template_dir))
            else:
                # Usar templates inline se diretorio nao existir
                loader = None

            self._env = Environment(
                loader=loader,
                autoescape=select_autoescape(['html', 'xml'])
            )

            # Adicionar filtros customizados
            self._env.filters['currency'] = self._filter_currency
            self._env.filters['percentage'] = self._filter_percentage
            self._env.filters['number'] = self._filter_number
            self._env.filters['date_br'] = self._filter_date_br

        return self._env

    def generate(
        self,
        kpis: Dict[str, Any],
        template: str = "daily.html",
        output_path: Optional[str] = None,
        title: Optional[str] = None
    ) -> str:
        """
        Gera relatorio HTML a partir de KPIs.

        Args:
            kpis: Dict com KPIs calculados (ex: {"vendas": {...}, "estoque": {...}})
            template: Nome do template a usar
            output_path: Caminho para salvar o arquivo HTML
            title: Titulo do relatorio

        Returns:
            HTML gerado como string
        """
        if title is None:
            title = f"Relatorio - {datetime.now().strftime('%d/%m/%Y')}"

        context = {
            "title": title,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "kpis": kpis,
        }

        # Tentar usar template do arquivo
        try:
            if self.template_dir and (self.template_dir / template).exists():
                tmpl = self.env.get_template(template)
                html = tmpl.render(**context)
            else:
                # Usar template inline padrao
                html = self._generate_default_report(context)
        except Exception as e:
            logger.error(f"Erro ao renderizar template: {e}")
            html = self._generate_default_report(context)

        # Salvar arquivo se especificado
        if output_path:
            self._save_report(html, output_path)

        return html

    def generate_daily(
        self,
        kpis: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Gera relatorio diario."""
        return self.generate(
            kpis=kpis,
            template="daily.html",
            output_path=output_path,
            title=f"Relatorio Diario - {datetime.now().strftime('%d/%m/%Y')}"
        )

    def generate_weekly(
        self,
        kpis: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Gera relatorio semanal."""
        return self.generate(
            kpis=kpis,
            template="weekly.html",
            output_path=output_path,
            title=f"Relatorio Semanal - {datetime.now().strftime('%d/%m/%Y')}"
        )

    def _generate_default_report(self, context: Dict[str, Any]) -> str:
        """Gera relatorio com template inline padrao."""
        kpis = context.get("kpis", {})

        # Construir HTML
        sections = []

        # Secao de Vendas
        if "vendas" in kpis:
            sections.append(self._render_section_vendas(kpis["vendas"]))

        # Secao de Compras
        if "compras" in kpis:
            sections.append(self._render_section_compras(kpis["compras"]))

        # Secao de Estoque
        if "estoque" in kpis:
            sections.append(self._render_section_estoque(kpis["estoque"]))

        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{context['title']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header .meta {{
            opacity: 0.9;
            font-size: 14px;
        }}
        .section {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .section h2 {{
            color: #1a237e;
            margin-top: 0;
            padding-bottom: 15px;
            border-bottom: 2px solid #e8eaf6;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .kpi-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #1a237e;
        }}
        .kpi-card .value {{
            font-size: 28px;
            font-weight: bold;
            color: #1a237e;
        }}
        .kpi-card .label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            text-transform: uppercase;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .text-right {{
            text-align: right;
        }}
        .text-center {{
            text-align: center;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}
        .badge-success {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        .badge-warning {{
            background: #fff3e0;
            color: #ef6c00;
        }}
        .badge-danger {{
            background: #ffebee;
            color: #c62828;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{context['title']}</h1>
            <div class="meta">Gerado em: {context['generated_at']}</div>
        </div>

        {''.join(sections)}

        <div class="footer">
            MMarra Data Hub - Agente Analista
        </div>
    </div>
</body>
</html>
"""
        return html

    def _render_section_vendas(self, kpis: Dict[str, Any]) -> str:
        """Renderiza secao de vendas."""
        faturamento = kpis.get("faturamento_total", {})
        ticket = kpis.get("ticket_medio", {})
        pedidos = kpis.get("qtd_pedidos", {})

        # Top vendedores
        top_vendedores_html = ""
        if "vendas_por_vendedor" in kpis:
            top = kpis["vendas_por_vendedor"].get("top", [])[:5]
            if top:
                rows = "".join([
                    f"<tr><td>{v.get('cod_vendedor', '-')}</td>"
                    f"<td class='text-right'>{v.get('faturamento_formatted', '-')}</td>"
                    f"<td class='text-center'>{v.get('qtd_pedidos', '-')}</td></tr>"
                    for v in top
                ])
                top_vendedores_html = f"""
                <h3>Top 5 Vendedores</h3>
                <table>
                    <thead>
                        <tr><th>Vendedor</th><th class="text-right">Faturamento</th><th class="text-center">Pedidos</th></tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                """

        return f"""
        <div class="section">
            <h2>Vendas</h2>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="value">{faturamento.get('formatted', '-')}</div>
                    <div class="label">Faturamento Total</div>
                </div>
                <div class="kpi-card">
                    <div class="value">{ticket.get('formatted', '-')}</div>
                    <div class="label">Ticket Medio</div>
                </div>
                <div class="kpi-card">
                    <div class="value">{pedidos.get('formatted', '-')}</div>
                    <div class="label">Pedidos</div>
                </div>
            </div>
            {top_vendedores_html}
        </div>
        """

    def _render_section_compras(self, kpis: Dict[str, Any]) -> str:
        """Renderiza secao de compras."""
        volume = kpis.get("volume_compras", {})
        pedidos = kpis.get("qtd_pedidos", {})
        conferencia = kpis.get("taxa_conferencia_wms", {})

        return f"""
        <div class="section">
            <h2>Compras</h2>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="value">{volume.get('formatted', '-')}</div>
                    <div class="label">Volume de Compras</div>
                </div>
                <div class="kpi-card">
                    <div class="value">{pedidos.get('formatted', '-')}</div>
                    <div class="label">Pedidos</div>
                </div>
                <div class="kpi-card">
                    <div class="value">{conferencia.get('formatted', '-')}</div>
                    <div class="label">Taxa Conferencia WMS</div>
                </div>
            </div>
        </div>
        """

    def _render_section_estoque(self, kpis: Dict[str, Any]) -> str:
        """Renderiza secao de estoque."""
        total_un = kpis.get("estoque_total_unidades", {})
        total_valor = kpis.get("estoque_total_valor", {})
        sem_estoque = kpis.get("produtos_sem_estoque", {})

        return f"""
        <div class="section">
            <h2>Estoque</h2>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="value">{total_un.get('formatted', '-')}</div>
                    <div class="label">Total em Unidades</div>
                </div>
                <div class="kpi-card">
                    <div class="value">{total_valor.get('formatted', '-')}</div>
                    <div class="label">Valor em Estoque</div>
                </div>
                <div class="kpi-card">
                    <div class="value">{sem_estoque.get('formatted', '-')}</div>
                    <div class="label">Produtos sem Estoque</div>
                </div>
            </div>
        </div>
        """

    def _save_report(self, html: str, output_path: str) -> None:
        """Salva relatorio em arquivo."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"Relatorio salvo em: {path}")

    # Filtros Jinja2
    @staticmethod
    def _filter_currency(value: float) -> str:
        """Filtro para formatar moeda."""
        if value is None:
            return "-"
        formatted = f"{value:,.2f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"

    @staticmethod
    def _filter_percentage(value: float) -> str:
        """Filtro para formatar porcentagem."""
        if value is None:
            return "-"
        return f"{value:.1f}%"

    @staticmethod
    def _filter_number(value: float) -> str:
        """Filtro para formatar numero."""
        if value is None:
            return "-"
        formatted = f"{value:,.0f}"
        formatted = formatted.replace(",", ".")
        return formatted

    @staticmethod
    def _filter_date_br(value: str) -> str:
        """Filtro para formatar data no padrao brasileiro."""
        if value is None:
            return "-"
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime("%d/%m/%Y")
        except Exception:
            return value
