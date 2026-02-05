# -*- coding: utf-8 -*-
"""
Calculador de KPIs de Compras

KPIs disponiveis:
- volume_compras: Valor total das compras
- custo_medio_produto: Custo medio por produto
- lead_time_fornecedor: Tempo medio de entrega por fornecedor
- pedidos_pendentes: Quantidade de pedidos aguardando
- taxa_conferencia_wms: % de pedidos conferidos no WMS
- top_fornecedores: Fornecedores com maior volume
- economia_cotacao: Economia obtida via cotacao

Retorna dados estruturados para consumo pelo Agente LLM.
"""

import logging
from datetime import date
from typing import Dict, Any, List, Optional, Union

import pandas as pd
import numpy as np

from .base import BaseKPI

logger = logging.getLogger(__name__)


class ComprasKPI(BaseKPI):
    """Calculador de KPIs de Compras."""

    REQUIRED_COLUMNS = ["NUNOTA", "VLRNOTA"]
    OPTIONAL_COLUMNS = [
        "DTNEG", "DTENTSAI", "CODPARC", "VLRUNIT",
        "CODPROD", "QTDNEG", "COD_SITUACAO"
    ]

    def get_name(self) -> str:
        return "compras"

    def get_available_metrics(self) -> List[str]:
        return [
            "volume_compras",
            "custo_medio_produto",
            "lead_time_fornecedor",
            "pedidos_pendentes",
            "taxa_conferencia_wms",
            "top_fornecedores",
            "economia_cotacao",
        ]

    def calculate_all(
        self,
        df: pd.DataFrame,
        data_inicio: Optional[Union[str, date]] = None,
        data_fim: Optional[Union[str, date]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calcula todos os KPIs de compras.

        Args:
            df: DataFrame com dados de compras (TGFCAB + TGFITE)
            data_inicio: Data inicial do periodo
            data_fim: Data final do periodo

        Returns:
            Dict estruturado com todos os KPIs
        """
        validation = self._validate_columns(df, self.REQUIRED_COLUMNS, self.OPTIONAL_COLUMNS)
        if not validation["valid"]:
            return self._build_response(df, {"error": "Colunas obrigatorias faltando"})

        if isinstance(data_inicio, date):
            data_inicio = data_inicio.strftime("%Y-%m-%d")
        if isinstance(data_fim, date):
            data_fim = data_fim.strftime("%Y-%m-%d")

        # Calcular KPIs
        kpis = {
            "volume_compras": self._calc_volume_compras(df),
            "qtd_pedidos": self._calc_qtd_pedidos(df),
        }

        # KPIs opcionais
        if "CODPROD" in df.columns and "VLRUNIT" in df.columns:
            kpis["custo_medio_produto"] = self._calc_custo_medio_produto(df)

        if "CODPARC" in df.columns:
            kpis["top_fornecedores"] = self._calc_top_fornecedores(df)

        if "DTNEG" in df.columns and "DTENTSAI" in df.columns:
            kpis["lead_time_fornecedor"] = self._calc_lead_time_fornecedor(df)

        if "COD_SITUACAO" in df.columns:
            kpis["taxa_conferencia_wms"] = self._calc_taxa_conferencia_wms(df)
            kpis["pedidos_por_status_wms"] = self._calc_pedidos_por_status_wms(df)

        if "DTNEG" in df.columns:
            kpis["compras_por_dia"] = self._calc_compras_por_dia(df)

        return self._build_response(df, kpis, data_inicio, data_fim)

    def _calc_volume_compras(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula volume total de compras."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])
        total = df_pedidos["VLRNOTA"].sum()

        return {
            "valor": float(total),
            "formatted": self._format_currency(total),
            "descricao": "Valor total das notas de compra"
        }

    def _calc_qtd_pedidos(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula quantidade de pedidos de compra."""
        qtd = df["NUNOTA"].nunique()

        return {
            "valor": int(qtd),
            "formatted": self._format_number(qtd),
            "descricao": "Quantidade de pedidos de compra"
        }

    def _calc_custo_medio_produto(
        self,
        df: pd.DataFrame,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Calcula custo medio por produto."""
        custos = df.groupby("CODPROD").agg({
            "VLRUNIT": "mean",
            "QTDNEG": "sum"
        }).reset_index()

        custos.columns = ["cod_produto", "custo_medio", "qtd_comprada"]
        custos = custos.sort_values("qtd_comprada", ascending=False)

        # Top N produtos mais comprados
        top = custos.head(top_n).to_dict(orient="records")

        for item in top:
            item["custo_medio_formatted"] = self._format_currency(item["custo_medio"])

        # Custo medio geral
        custo_geral = df["VLRUNIT"].mean()

        return {
            "custo_medio_geral": float(custo_geral),
            "custo_medio_geral_formatted": self._format_currency(custo_geral),
            "top_produtos": top,
            "total_produtos": len(custos),
            "descricao": f"Custo medio por produto (top {top_n} mais comprados)"
        }

    def _calc_lead_time_fornecedor(
        self,
        df: pd.DataFrame,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Calcula lead time medio por fornecedor."""
        df_calc = df.drop_duplicates(subset=["NUNOTA"]).copy()

        # Converter datas
        df_calc["DTNEG"] = pd.to_datetime(df_calc["DTNEG"], errors='coerce')
        df_calc["DTENTSAI"] = pd.to_datetime(df_calc["DTENTSAI"], errors='coerce')

        # Calcular dias
        df_calc["lead_time_dias"] = (df_calc["DTENTSAI"] - df_calc["DTNEG"]).dt.days

        # Remover valores negativos ou nulos
        df_calc = df_calc[df_calc["lead_time_dias"] >= 0]

        if df_calc.empty:
            return {
                "lead_time_medio_geral": 0,
                "fornecedores": [],
                "descricao": "Sem dados de lead time disponiveis"
            }

        # Lead time por fornecedor
        lead_times = df_calc.groupby("CODPARC").agg({
            "lead_time_dias": "mean",
            "NUNOTA": "count"
        }).reset_index()

        lead_times.columns = ["cod_fornecedor", "lead_time_medio", "qtd_pedidos"]
        lead_times = lead_times.sort_values("qtd_pedidos", ascending=False)

        # Top N fornecedores
        top = lead_times.head(top_n).to_dict(orient="records")

        for item in top:
            item["lead_time_medio"] = round(item["lead_time_medio"], 1)

        # Lead time geral
        lead_time_geral = df_calc["lead_time_dias"].mean()

        return {
            "lead_time_medio_geral": round(float(lead_time_geral), 1),
            "fornecedores": top,
            "total_fornecedores": len(lead_times),
            "descricao": "Tempo medio em dias entre pedido e entrada da mercadoria"
        }

    def _calc_taxa_conferencia_wms(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula taxa de conferencia do WMS."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])

        total = len(df_pedidos)
        if total == 0:
            return {
                "valor": 0,
                "formatted": self._format_percentage(0),
                "descricao": "Sem pedidos para calcular"
            }

        # Status de conferencia WMS (conforme mapeamento)
        # 19 = Armazenado (conferido e finalizado)
        # 12-18 = Em processo de conferencia
        conferidos = len(df_pedidos[df_pedidos["COD_SITUACAO"] == 19])
        em_conferencia = len(df_pedidos[df_pedidos["COD_SITUACAO"].isin([12, 13, 14, 15, 16, 17, 18])])

        taxa = self._safe_divide(conferidos, total) * 100

        return {
            "valor": float(taxa),
            "formatted": self._format_percentage(taxa),
            "conferidos": conferidos,
            "em_conferencia": em_conferencia,
            "total": total,
            "descricao": "Percentual de pedidos com conferencia WMS finalizada"
        }

    def _calc_pedidos_por_status_wms(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula quantidade de pedidos por status WMS."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])

        # Mapeamento de status WMS
        STATUS_MAP = {
            -1: "Nao Enviado",
            3: "Aguardando Conferencia",
            4: "Em Conferencia",
            5: "Conferencia Divergente",
            6: "Em Recebimento",
            12: "Aguardando Armazenagem",
            13: "Em Armazenagem",
            14: "Armazenagem Parcial",
            15: "Aguardando Liberacao",
            16: "Liberado",
            17: "Em Processamento",
            18: "Processamento Parcial",
            19: "Armazenado",
            100: "Cancelado"
        }

        contagem = df_pedidos.groupby("COD_SITUACAO").size().reset_index()
        contagem.columns = ["cod_situacao", "quantidade"]

        # Adicionar descricao
        contagem["status"] = contagem["cod_situacao"].map(STATUS_MAP).fillna("Desconhecido")

        resultado = contagem.to_dict(orient="records")

        return {
            "por_status": resultado,
            "total": len(df_pedidos),
            "descricao": "Quantidade de pedidos por status WMS"
        }

    def _calc_top_fornecedores(
        self,
        df: pd.DataFrame,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Calcula top fornecedores por volume de compras."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"])

        vendas = df_pedidos.groupby("CODPARC").agg({
            "VLRNOTA": "sum",
            "NUNOTA": "count"
        }).reset_index()

        vendas.columns = ["cod_fornecedor", "volume_compras", "qtd_pedidos"]
        vendas = vendas.sort_values("volume_compras", ascending=False)

        # Top N
        top = vendas.head(top_n).to_dict(orient="records")

        for item in top:
            item["volume_compras_formatted"] = self._format_currency(item["volume_compras"])

        return {
            "top": top,
            "total_fornecedores": len(vendas),
            "descricao": f"Top {top_n} fornecedores por volume de compras"
        }

    def _calc_compras_por_dia(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula compras por dia (para graficos)."""
        df_pedidos = df.drop_duplicates(subset=["NUNOTA"]).copy()

        df_pedidos["DTNEG"] = pd.to_datetime(df_pedidos["DTNEG"], errors='coerce')

        compras_dia = df_pedidos.groupby(df_pedidos["DTNEG"].dt.date).agg({
            "VLRNOTA": "sum",
            "NUNOTA": "count"
        }).reset_index()

        compras_dia.columns = ["data", "volume", "qtd_pedidos"]

        dados = []
        for _, row in compras_dia.iterrows():
            dados.append({
                "data": str(row["data"]),
                "volume": float(row["volume"]),
                "qtd_pedidos": int(row["qtd_pedidos"])
            })

        return {
            "dados": dados,
            "total_dias": len(dados),
            "descricao": "Volume e quantidade de compras por dia"
        }
