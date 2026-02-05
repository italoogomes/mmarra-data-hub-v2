# -*- coding: utf-8 -*-
"""
Preparacao de Dados para Dashboards

Transforma dados de KPIs em estruturas otimizadas para visualizacao.
Suporta Plotly, Streamlit, e outras bibliotecas de visualizacao.

Exemplo de uso:
    from src.agents.analyst.dashboards import DashboardDataPrep

    prep = DashboardDataPrep()

    # Preparar serie temporal para grafico de linha
    dados_linha = prep.prepare_time_series(df, date_col="DTNEG", value_col="VLRNOTA")

    # Preparar ranking para grafico de barras
    dados_barra = prep.prepare_ranking(df, group_col="CODVEND", value_col="VLRNOTA", top_n=10)

    # Calcular curva ABC
    dados_abc = prep.prepare_curva_abc(df, item_col="CODPROD", value_col="VLRNOTA")
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DashboardDataPrep:
    """
    Prepara dados para visualizacao em dashboards.

    Metodos disponiveis:
    - prepare_time_series: Serie temporal para graficos de linha
    - prepare_ranking: Ranking para graficos de barras
    - prepare_curva_abc: Curva ABC para graficos de Pareto
    - prepare_pie_chart: Dados para graficos de pizza
    - prepare_heatmap: Dados para mapas de calor
    - prepare_comparison: Comparacao entre periodos
    """

    def prepare_time_series(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        freq: str = 'D',
        agg_func: str = 'sum',
        fill_missing: bool = True
    ) -> Dict[str, Any]:
        """
        Prepara dados para grafico de serie temporal.

        Args:
            df: DataFrame com os dados
            date_col: Nome da coluna de data
            value_col: Nome da coluna de valor
            freq: Frequencia de agregacao ('D'=diario, 'W'=semanal, 'M'=mensal)
            agg_func: Funcao de agregacao ('sum', 'mean', 'count')
            fill_missing: Se True, preenche datas faltantes com zero

        Returns:
            Dict com dados prontos para plotagem
        """
        df_copy = df.copy()

        # Converter data
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col])

        # Agrupar por periodo
        df_copy.set_index(date_col, inplace=True)

        if agg_func == 'sum':
            series = df_copy[value_col].resample(freq).sum()
        elif agg_func == 'mean':
            series = df_copy[value_col].resample(freq).mean()
        elif agg_func == 'count':
            series = df_copy[value_col].resample(freq).count()
        else:
            series = df_copy[value_col].resample(freq).sum()

        # Preencher valores faltantes
        if fill_missing:
            series = series.fillna(0)

        # Converter para listas
        dates = [d.strftime('%Y-%m-%d') for d in series.index]
        values = series.values.tolist()

        return {
            "type": "time_series",
            "dates": dates,
            "values": values,
            "freq": freq,
            "agg_func": agg_func,
            "total": sum(values),
            "mean": np.mean(values) if values else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
        }

    def prepare_ranking(
        self,
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
        top_n: int = 10,
        agg_func: str = 'sum',
        ascending: bool = False,
        include_others: bool = True
    ) -> Dict[str, Any]:
        """
        Prepara dados para grafico de ranking (barras horizontais).

        Args:
            df: DataFrame com os dados
            group_col: Coluna para agrupamento
            value_col: Coluna de valor
            top_n: Numero de itens no ranking
            agg_func: Funcao de agregacao
            ascending: Se True, ordena do menor para maior
            include_others: Se True, agrupa demais itens em "Outros"

        Returns:
            Dict com dados prontos para plotagem
        """
        # Agrupar
        if agg_func == 'sum':
            grouped = df.groupby(group_col)[value_col].sum()
        elif agg_func == 'mean':
            grouped = df.groupby(group_col)[value_col].mean()
        elif agg_func == 'count':
            grouped = df.groupby(group_col)[value_col].count()
        else:
            grouped = df.groupby(group_col)[value_col].sum()

        # Ordenar
        grouped = grouped.sort_values(ascending=ascending)

        # Top N
        if include_others and len(grouped) > top_n:
            top = grouped.tail(top_n) if not ascending else grouped.head(top_n)
            others = grouped.iloc[:-top_n].sum() if not ascending else grouped.iloc[top_n:].sum()

            labels = top.index.tolist()
            values = top.values.tolist()

            if others > 0:
                labels.insert(0 if ascending else len(labels), "Outros")
                values.insert(0 if ascending else len(values), others)
        else:
            top = grouped.tail(top_n) if not ascending else grouped.head(top_n)
            labels = top.index.tolist()
            values = top.values.tolist()

        # Inverter para exibicao correta em graficos de barra horizontal
        if not ascending:
            labels = labels[::-1]
            values = values[::-1]

        return {
            "type": "ranking",
            "labels": labels,
            "values": values,
            "total_items": len(grouped),
            "showing": len(labels),
            "total_value": grouped.sum(),
        }

    def prepare_curva_abc(
        self,
        df: pd.DataFrame,
        item_col: str,
        value_col: str,
        thresholds: Tuple[float, float] = (80, 95)
    ) -> Dict[str, Any]:
        """
        Prepara dados para curva ABC (Pareto).

        Args:
            df: DataFrame com os dados
            item_col: Coluna de identificacao do item
            value_col: Coluna de valor
            thresholds: Limites para classes A e B (default: 80%, 95%)

        Returns:
            Dict com dados da curva ABC
        """
        # Agrupar por item
        valores = df.groupby(item_col)[value_col].sum().reset_index()
        valores = valores.sort_values(value_col, ascending=False)

        # Calcular percentuais
        total = valores[value_col].sum()
        valores['percentual'] = valores[value_col] / total * 100
        valores['percentual_acum'] = valores['percentual'].cumsum()

        # Classificar
        def classificar(pct_acum):
            if pct_acum <= thresholds[0]:
                return 'A'
            elif pct_acum <= thresholds[1]:
                return 'B'
            return 'C'

        valores['classe'] = valores['percentual_acum'].apply(classificar)

        # Resumo por classe
        resumo = valores.groupby('classe').agg({
            item_col: 'count',
            value_col: 'sum',
            'percentual': 'sum'
        }).reset_index()

        resumo.columns = ['classe', 'qtd_itens', 'valor', 'percentual']

        # Dados para grafico de Pareto
        pareto_data = {
            "items": valores[item_col].tolist()[:50],  # Limitar a 50 itens
            "values": valores[value_col].tolist()[:50],
            "percentual_acum": valores['percentual_acum'].tolist()[:50],
            "classes": valores['classe'].tolist()[:50],
        }

        # Resumo
        classes_resumo = {}
        for _, row in resumo.iterrows():
            classe = row['classe']
            classes_resumo[classe] = {
                "qtd_itens": int(row['qtd_itens']),
                "valor": float(row['valor']),
                "percentual": float(row['percentual']),
                "percentual_itens": float(row['qtd_itens'] / len(valores) * 100)
            }

        return {
            "type": "curva_abc",
            "thresholds": thresholds,
            "classes": classes_resumo,
            "pareto": pareto_data,
            "total_itens": len(valores),
            "total_valor": float(total),
        }

    def prepare_pie_chart(
        self,
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
        top_n: int = 5,
        include_others: bool = True
    ) -> Dict[str, Any]:
        """
        Prepara dados para grafico de pizza.

        Args:
            df: DataFrame com os dados
            group_col: Coluna para agrupamento
            value_col: Coluna de valor
            top_n: Numero de fatias principais
            include_others: Se True, agrupa demais em "Outros"

        Returns:
            Dict com dados prontos para grafico de pizza
        """
        grouped = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)

        total = grouped.sum()

        if include_others and len(grouped) > top_n:
            top = grouped.head(top_n)
            others = grouped.iloc[top_n:].sum()

            labels = top.index.tolist() + ["Outros"]
            values = top.values.tolist() + [others]
        else:
            labels = grouped.head(top_n).index.tolist()
            values = grouped.head(top_n).values.tolist()

        # Calcular percentuais
        percentuais = [v / total * 100 for v in values]

        return {
            "type": "pie_chart",
            "labels": labels,
            "values": values,
            "percentuais": percentuais,
            "total": float(total),
        }

    def prepare_heatmap(
        self,
        df: pd.DataFrame,
        row_col: str,
        col_col: str,
        value_col: str,
        agg_func: str = 'sum'
    ) -> Dict[str, Any]:
        """
        Prepara dados para mapa de calor.

        Args:
            df: DataFrame com os dados
            row_col: Coluna para linhas
            col_col: Coluna para colunas
            value_col: Coluna de valor
            agg_func: Funcao de agregacao

        Returns:
            Dict com dados para heatmap
        """
        # Criar pivot table
        if agg_func == 'sum':
            pivot = df.pivot_table(index=row_col, columns=col_col, values=value_col, aggfunc='sum')
        elif agg_func == 'mean':
            pivot = df.pivot_table(index=row_col, columns=col_col, values=value_col, aggfunc='mean')
        else:
            pivot = df.pivot_table(index=row_col, columns=col_col, values=value_col, aggfunc='sum')

        pivot = pivot.fillna(0)

        return {
            "type": "heatmap",
            "row_labels": pivot.index.tolist(),
            "col_labels": pivot.columns.tolist(),
            "values": pivot.values.tolist(),
            "min_value": float(pivot.values.min()),
            "max_value": float(pivot.values.max()),
        }

    def prepare_comparison(
        self,
        df_atual: pd.DataFrame,
        df_anterior: pd.DataFrame,
        value_col: str,
        agg_func: str = 'sum'
    ) -> Dict[str, Any]:
        """
        Prepara comparacao entre dois periodos.

        Args:
            df_atual: DataFrame do periodo atual
            df_anterior: DataFrame do periodo anterior
            value_col: Coluna de valor
            agg_func: Funcao de agregacao

        Returns:
            Dict com dados de comparacao
        """
        if agg_func == 'sum':
            atual = df_atual[value_col].sum()
            anterior = df_anterior[value_col].sum()
        elif agg_func == 'mean':
            atual = df_atual[value_col].mean()
            anterior = df_anterior[value_col].mean()
        elif agg_func == 'count':
            atual = len(df_atual)
            anterior = len(df_anterior)
        else:
            atual = df_atual[value_col].sum()
            anterior = df_anterior[value_col].sum()

        # Calcular variacao
        if anterior == 0:
            variacao_pct = 100 if atual > 0 else 0
        else:
            variacao_pct = (atual - anterior) / anterior * 100

        variacao_abs = atual - anterior

        return {
            "type": "comparison",
            "atual": float(atual),
            "anterior": float(anterior),
            "variacao_absoluta": float(variacao_abs),
            "variacao_percentual": float(variacao_pct),
            "tendencia": "alta" if variacao_pct > 0 else "baixa" if variacao_pct < 0 else "estavel",
        }

    def prepare_kpi_summary(
        self,
        kpis: Dict[str, Any],
        include_sparklines: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Prepara resumo de KPIs para cards de dashboard.

        Args:
            kpis: Dict com KPIs calculados
            include_sparklines: Se True, inclui mini graficos

        Returns:
            Lista de dicts prontos para renderizacao em cards
        """
        cards = []

        # Processar KPIs de vendas
        if "vendas" in kpis:
            v = kpis["vendas"]
            if "faturamento_total" in v:
                cards.append({
                    "title": "Faturamento",
                    "value": v["faturamento_total"].get("formatted", "-"),
                    "icon": "dollar-sign",
                    "color": "blue",
                })
            if "ticket_medio" in v:
                cards.append({
                    "title": "Ticket Medio",
                    "value": v["ticket_medio"].get("formatted", "-"),
                    "icon": "receipt",
                    "color": "green",
                })
            if "qtd_pedidos" in v:
                cards.append({
                    "title": "Pedidos",
                    "value": v["qtd_pedidos"].get("formatted", "-"),
                    "icon": "shopping-cart",
                    "color": "purple",
                })

        # Processar KPIs de estoque
        if "estoque" in kpis:
            e = kpis["estoque"]
            if "produtos_sem_estoque" in e:
                cards.append({
                    "title": "Sem Estoque",
                    "value": e["produtos_sem_estoque"].get("formatted", "-"),
                    "icon": "alert-triangle",
                    "color": "red",
                })

        return cards
