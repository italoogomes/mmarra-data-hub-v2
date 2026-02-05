# -*- coding: utf-8 -*-
"""
Calculador de KPIs de Vendas

KPIs disponiveis:
- faturamento_total: Soma do valor das notas
- ticket_medio: Faturamento / Numero de pedidos
- qtd_pedidos: Contagem de pedidos unicos
- vendas_por_vendedor: Faturamento agrupado por vendedor
- vendas_por_cliente: Faturamento agrupado por cliente
- taxa_desconto: % de desconto sobre o faturamento
- crescimento_mom: Crescimento mes a mes
- top_produtos: Produtos mais vendidos
- curva_abc_clientes: Classificacao ABC de clientes

Retorna dados estruturados para consumo pelo Agente LLM.
"""

import logging
from datetime import date
from typing import Dict, Any, List, Optional, Union

import pandas as pd
import numpy as np

from .base import BaseKPI

logger = logging.getLogger(__name__)


class VendasKPI(BaseKPI):
    """Calculador de KPIs de Vendas."""

    REQUIRED_COLUMNS = ["NUNOTA", "VLRNOTA"]
    OPTIONAL_COLUMNS = [
        "DTNEG", "CODVEND", "CODPARC", "VLRDESCTOT",
        "CODPROD", "QTDNEG", "VLRTOT"
    ]

    def get_name(self) -> str:
        return "vendas"

    def get_available_metrics(self) -> List[str]:
        return [
            "faturamento_total",
            "ticket_medio",
            "qtd_pedidos",
            "vendas_por_vendedor",
            "vendas_por_cliente",
            "taxa_desconto",
            "crescimento_mom",
            "top_produtos",
            "curva_abc_clientes",
        ]

    def calculate_all(
        self,
        df: pd.DataFrame,
        data_inicio: Optional[Union[str, date]] = None,
        data_fim: Optional[Union[str, date]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calcula todos os KPIs de vendas.

        Args:
            df: DataFrame com dados de vendas (TGFCAB + TGFITE)
            data_inicio: Data inicial do periodo
            data_fim: Data final do periodo

        Returns:
            Dict estruturado com todos os KPIs
        """
        # Validar colunas
        validation = self._validate_columns(df, self.REQUIRED_COLUMNS, self.OPTIONAL_COLUMNS)
        if not validation["valid"]:
            return self._build_response(df, {"error": "Colunas obrigatorias faltando"})

        # Converter datas para string se necessario
        if isinstance(data_inicio, date):
            data_inicio = data_inicio.strftime("%Y-%m-%d")
        if isinstance(data_fim, date):
            data_fim = data_fim.strftime("%Y-%m-%d")

        # Calcular KPIs
        kpis = {
            "faturamento_total": self._calc_faturamento_total(df),
            "ticket_medio": self._calc_ticket_medio(df),
            "qtd_pedidos": self._calc_qtd_pedidos(df),
        }

        # KPIs opcionais (dependem de colunas especificas)
        if "CODVEND" in df.columns:
            kpis["vendas_por_vendedor"] = self._calc_vendas_por_vendedor(df)

        if "CODPARC" in df.columns:
            kpis["vendas_por_cliente"] = self._calc_vendas_por_cliente(df)
            kpis["curva_abc_clientes"] = self._calc_curva_abc_clientes(df)

        if "VLRDESCTOT" in df.columns:
            kpis["taxa_desconto"] = self._calc_taxa_desconto(df)

        if "CODPROD" in df.columns and "QTDNEG" in df.columns:
            kpis["top_produtos"] = self._calc_top_produtos(df)

        if "DTNEG" in df.columns:
            kpis["crescimento_mom"] = self._calc_crescimento_mom(df)
            kpis["vendas_por_dia"] = self._calc_vendas_por_dia(df)

        return self._build_response(df, kpis, data_inicio, data_fim)

    def _calc_faturamento_total(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula faturamento total."""
        # Agrupar por NUNOTA para evitar duplicatas de itens
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])
        total = df_pedidos["VLRNOTA"].sum()

        return {
            "valor": float(total),
            "formatted": self._format_currency(total),
            "descricao": "Soma do valor de todas as notas fiscais"
        }

    def _calc_ticket_medio(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula ticket medio."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])
        total = df_pedidos["VLRNOTA"].sum()
        qtd = len(df_pedidos)
        ticket = self._safe_divide(total, qtd)

        return {
            "valor": float(ticket),
            "formatted": self._format_currency(ticket),
            "descricao": "Valor medio por pedido"
        }

    def _calc_qtd_pedidos(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula quantidade de pedidos."""
        qtd = df["NUNOTA"].nunique()

        return {
            "valor": int(qtd),
            "formatted": self._format_number(qtd),
            "descricao": "Quantidade de pedidos unicos"
        }

    def _calc_vendas_por_vendedor(
        self,
        df: pd.DataFrame,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Calcula vendas agrupadas por vendedor."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])

        vendas = df_pedidos.groupby("CODVEND").agg({
            "VLRNOTA": "sum",
            "NUNOTA": "count"
        }).reset_index()

        vendas.columns = ["cod_vendedor", "faturamento", "qtd_pedidos"]
        vendas = vendas.sort_values("faturamento", ascending=False)

        # Top N
        top = vendas.head(top_n).to_dict(orient="records")

        # Formatar valores
        for item in top:
            item["faturamento_formatted"] = self._format_currency(item["faturamento"])

        return {
            "top": top,
            "total_vendedores": len(vendas),
            "descricao": f"Top {top_n} vendedores por faturamento"
        }

    def _calc_vendas_por_cliente(
        self,
        df: pd.DataFrame,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Calcula vendas agrupadas por cliente."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])

        vendas = df_pedidos.groupby("CODPARC").agg({
            "VLRNOTA": "sum",
            "NUNOTA": "count"
        }).reset_index()

        vendas.columns = ["cod_cliente", "faturamento", "qtd_pedidos"]
        vendas = vendas.sort_values("faturamento", ascending=False)

        # Top N
        top = vendas.head(top_n).to_dict(orient="records")

        for item in top:
            item["faturamento_formatted"] = self._format_currency(item["faturamento"])

        return {
            "top": top,
            "total_clientes": len(vendas),
            "descricao": f"Top {top_n} clientes por faturamento"
        }

    def _calc_taxa_desconto(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula taxa de desconto sobre o faturamento."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])

        total_desconto = df_pedidos["VLRDESCTOT"].fillna(0).sum()
        total_faturamento = df_pedidos["VLRNOTA"].sum()

        taxa = self._safe_divide(total_desconto, total_faturamento) * 100

        return {
            "valor": float(taxa),
            "formatted": self._format_percentage(taxa),
            "total_desconto": float(total_desconto),
            "total_desconto_formatted": self._format_currency(total_desconto),
            "descricao": "Percentual de desconto sobre o faturamento bruto"
        }

    def _calc_crescimento_mom(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula crescimento mes a mes."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"]).copy()

        # Converter data
        df_pedidos["DTNEG"] = pd.to_datetime(df_pedidos["DTNEG"], errors='coerce')
        df_pedidos["mes"] = df_pedidos["DTNEG"].dt.to_period("M")

        # Agrupar por mes
        vendas_mes = df_pedidos.groupby("mes")["VLRNOTA"].sum().reset_index()
        vendas_mes = vendas_mes.sort_values("mes")

        if len(vendas_mes) < 2:
            return {
                "valor": 0,
                "formatted": self._format_percentage(0),
                "historico": [],
                "descricao": "Dados insuficientes para calcular crescimento"
            }

        # Calcular crescimento
        vendas_mes["crescimento"] = vendas_mes["VLRNOTA"].pct_change() * 100

        # Ultimo crescimento
        ultimo_cresc = vendas_mes["crescimento"].iloc[-1]
        if pd.isna(ultimo_cresc):
            ultimo_cresc = 0

        # Historico
        historico = []
        for _, row in vendas_mes.iterrows():
            historico.append({
                "mes": str(row["mes"]),
                "faturamento": float(row["VLRNOTA"]),
                "crescimento": float(row["crescimento"]) if pd.notna(row["crescimento"]) else None
            })

        return {
            "valor": float(ultimo_cresc),
            "formatted": self._format_percentage(ultimo_cresc),
            "historico": historico,
            "descricao": "Crescimento percentual em relacao ao mes anterior"
        }

    def _calc_top_produtos(
        self,
        df: pd.DataFrame,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Calcula produtos mais vendidos."""
        # Usar colunas de itens (nao agrupar por NUNOTA aqui)
        vendas = df.groupby("CODPROD").agg({
            "QTDNEG": "sum",
            "VLRTOT": "sum" if "VLRTOT" in df.columns else "count"
        }).reset_index()

        if "VLRTOT" not in df.columns:
            vendas.columns = ["cod_produto", "qtd_vendida", "qtd_registros"]
        else:
            vendas.columns = ["cod_produto", "qtd_vendida", "valor_total"]

        vendas = vendas.sort_values("qtd_vendida", ascending=False)

        # Top N
        top = vendas.head(top_n).to_dict(orient="records")

        return {
            "top": top,
            "total_produtos": len(vendas),
            "descricao": f"Top {top_n} produtos mais vendidos por quantidade"
        }

    def _calc_curva_abc_clientes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula curva ABC de clientes."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])

        vendas = df_pedidos.groupby("CODPARC")["VLRNOTA"].sum().reset_index()
        vendas.columns = ["cod_cliente", "faturamento"]
        vendas = vendas.sort_values("faturamento", ascending=False)

        # Calcular percentual acumulado
        total = vendas["faturamento"].sum()
        vendas["percentual"] = vendas["faturamento"] / total * 100
        vendas["percentual_acum"] = vendas["percentual"].cumsum()

        # Classificar ABC
        def classificar(pct_acum):
            if pct_acum <= 80:
                return "A"
            elif pct_acum <= 95:
                return "B"
            else:
                return "C"

        vendas["classe"] = vendas["percentual_acum"].apply(classificar)

        # Resumo por classe
        resumo = vendas.groupby("classe").agg({
            "cod_cliente": "count",
            "faturamento": "sum"
        }).reset_index()

        resumo.columns = ["classe", "qtd_clientes", "faturamento"]

        resultado = {}
        for _, row in resumo.iterrows():
            classe = row["classe"]
            resultado[f"classe_{classe}"] = {
                "qtd_clientes": int(row["qtd_clientes"]),
                "faturamento": float(row["faturamento"]),
                "faturamento_formatted": self._format_currency(row["faturamento"]),
                "percentual": float(row["faturamento"] / total * 100)
            }

        resultado["descricao"] = "Curva ABC: A=80% do faturamento, B=15%, C=5%"
        resultado["total_clientes"] = len(vendas)

        return resultado

    def _calc_vendas_por_dia(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula vendas por dia (para graficos)."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"]).copy()

        df_pedidos["DTNEG"] = pd.to_datetime(df_pedidos["DTNEG"], errors='coerce')

        vendas_dia = df_pedidos.groupby(df_pedidos["DTNEG"].dt.date).agg({
            "VLRNOTA": "sum",
            "NUNOTA": "count"
        }).reset_index()

        vendas_dia.columns = ["data", "faturamento", "qtd_pedidos"]

        # Converter para lista de dicts
        dados = []
        for _, row in vendas_dia.iterrows():
            dados.append({
                "data": str(row["data"]),
                "faturamento": float(row["faturamento"]),
                "qtd_pedidos": int(row["qtd_pedidos"])
            })

        return {
            "dados": dados,
            "total_dias": len(dados),
            "descricao": "Faturamento e quantidade de pedidos por dia"
        }
