# -*- coding: utf-8 -*-
"""
Calculador de KPIs de Estoque

KPIs disponiveis:
- estoque_total_valor: Valor total em estoque (R$)
- estoque_total_unidades: Quantidade total em estoque
- giro_estoque: Giro de estoque (vendas / estoque medio)
- produtos_sem_estoque: Produtos com estoque zerado
- cobertura_estoque: Dias de cobertura do estoque
- divergencia_erp_wms: Diferenca entre ERP e WMS
- taxa_ocupacao_wms: % de ocupacao dos enderecos WMS
- produtos_parados: Produtos sem movimentacao
- curva_abc_estoque: Classificacao ABC do estoque

Retorna dados estruturados para consumo pelo Agente LLM.
"""

import logging
from datetime import date
from typing import Dict, Any, List, Optional, Union

import pandas as pd
import numpy as np

from .base import BaseKPI

logger = logging.getLogger(__name__)


class EstoqueKPI(BaseKPI):
    """Calculador de KPIs de Estoque."""

    REQUIRED_COLUMNS = ["CODPROD", "ESTOQUE"]
    OPTIONAL_COLUMNS = [
        "DISPONIVEL", "RESERVADO", "VLRUNIT", "CODLOCAL",
        "CONTROLE", "CODEMP", "DESCRPROD"
    ]

    def get_name(self) -> str:
        return "estoque"

    def get_available_metrics(self) -> List[str]:
        return [
            "estoque_total_valor",
            "estoque_total_unidades",
            "giro_estoque",
            "produtos_sem_estoque",
            "cobertura_estoque",
            "divergencia_erp_wms",
            "taxa_ocupacao_wms",
            "produtos_parados",
            "curva_abc_estoque",
        ]

    def calculate_all(
        self,
        df: pd.DataFrame,
        data_inicio: Optional[Union[str, date]] = None,
        data_fim: Optional[Union[str, date]] = None,
        df_vendas: Optional[pd.DataFrame] = None,
        df_wms: Optional[pd.DataFrame] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calcula todos os KPIs de estoque.

        Args:
            df: DataFrame com dados de estoque (TGFEST)
            data_inicio: Data inicial do periodo
            data_fim: Data final do periodo
            df_vendas: DataFrame com vendas (para calcular giro)
            df_wms: DataFrame com estoque WMS (para calcular divergencia)

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

        # Calcular KPIs basicos
        kpis = {
            "estoque_total_unidades": self._calc_estoque_total_unidades(df),
            "produtos_com_estoque": self._calc_produtos_com_estoque(df),
            "produtos_sem_estoque": self._calc_produtos_sem_estoque(df),
        }

        # KPIs que precisam de VLRUNIT
        if "VLRUNIT" in df.columns:
            kpis["estoque_total_valor"] = self._calc_estoque_total_valor(df)
            kpis["curva_abc_estoque"] = self._calc_curva_abc_estoque(df)

        # KPIs que precisam de RESERVADO
        if "RESERVADO" in df.columns:
            kpis["estoque_reservado"] = self._calc_estoque_reservado(df)

        # KPIs que precisam de DISPONIVEL
        if "DISPONIVEL" in df.columns:
            kpis["estoque_disponivel"] = self._calc_estoque_disponivel(df)

        # KPIs que precisam de CODLOCAL
        if "CODLOCAL" in df.columns:
            kpis["estoque_por_local"] = self._calc_estoque_por_local(df)

        # KPIs que precisam de CODEMP
        if "CODEMP" in df.columns:
            kpis["estoque_por_empresa"] = self._calc_estoque_por_empresa(df)

        # Giro de estoque (precisa de df_vendas)
        if df_vendas is not None:
            kpis["giro_estoque"] = self._calc_giro_estoque(df, df_vendas)

        # Divergencia ERP x WMS (precisa de df_wms)
        if df_wms is not None:
            kpis["divergencia_erp_wms"] = self._calc_divergencia_erp_wms(df, df_wms)

        return self._build_response(df, kpis, data_inicio, data_fim)

    def _calc_estoque_total_unidades(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula estoque total em unidades."""
        total = df["ESTOQUE"].sum()

        return {
            "valor": float(total),
            "formatted": self._format_number(total),
            "descricao": "Quantidade total em estoque (todas as unidades)"
        }

    def _calc_estoque_total_valor(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula valor total do estoque."""
        df_calc = df.copy()
        df_calc["valor_estoque"] = df_calc["ESTOQUE"] * df_calc["VLRUNIT"]
        total = df_calc["valor_estoque"].sum()

        return {
            "valor": float(total),
            "formatted": self._format_currency(total),
            "descricao": "Valor total do estoque (quantidade x custo unitario)"
        }

    def _calc_produtos_com_estoque(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula quantidade de produtos com estoque."""
        df_positivo = df[df["ESTOQUE"] > 0]
        qtd = df_positivo["CODPROD"].nunique()

        return {
            "valor": int(qtd),
            "formatted": self._format_number(qtd),
            "descricao": "Quantidade de produtos com estoque positivo"
        }

    def _calc_produtos_sem_estoque(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula produtos com estoque zerado ou negativo."""
        df_zerado = df[df["ESTOQUE"] <= 0]
        qtd = df_zerado["CODPROD"].nunique()

        # Listar top 10 produtos zerados
        produtos_zerados = df_zerado.drop_duplicates(subset=["CODPROD"])

        if "DESCRPROD" in df_zerado.columns:
            top = produtos_zerados[["CODPROD", "DESCRPROD", "ESTOQUE"]].head(10).to_dict(orient="records")
        else:
            top = produtos_zerados[["CODPROD", "ESTOQUE"]].head(10).to_dict(orient="records")

        return {
            "valor": int(qtd),
            "formatted": self._format_number(qtd),
            "exemplos": top,
            "descricao": "Quantidade de produtos com estoque zerado ou negativo"
        }

    def _calc_estoque_reservado(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula estoque total reservado."""
        total = df["RESERVADO"].fillna(0).sum()

        return {
            "valor": float(total),
            "formatted": self._format_number(total),
            "descricao": "Quantidade total reservada (empenhos, pedidos, etc)"
        }

    def _calc_estoque_disponivel(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula estoque disponivel para venda."""
        total = df["DISPONIVEL"].sum()

        return {
            "valor": float(total),
            "formatted": self._format_number(total),
            "descricao": "Quantidade disponivel para venda (estoque - reservado)"
        }

    def _calc_estoque_por_local(
        self,
        df: pd.DataFrame,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Calcula estoque agrupado por local."""
        estoque_local = df.groupby("CODLOCAL").agg({
            "ESTOQUE": "sum",
            "CODPROD": "nunique"
        }).reset_index()

        estoque_local.columns = ["cod_local", "estoque_total", "qtd_produtos"]
        estoque_local = estoque_local.sort_values("estoque_total", ascending=False)

        top = estoque_local.head(top_n).to_dict(orient="records")

        return {
            "por_local": top,
            "total_locais": len(estoque_local),
            "descricao": f"Estoque agrupado por local (top {top_n})"
        }

    def _calc_estoque_por_empresa(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula estoque agrupado por empresa."""
        estoque_emp = df.groupby("CODEMP").agg({
            "ESTOQUE": "sum",
            "CODPROD": "nunique"
        }).reset_index()

        estoque_emp.columns = ["cod_empresa", "estoque_total", "qtd_produtos"]

        resultado = estoque_emp.to_dict(orient="records")

        return {
            "por_empresa": resultado,
            "total_empresas": len(estoque_emp),
            "descricao": "Estoque agrupado por empresa/filial"
        }

    def _calc_curva_abc_estoque(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula curva ABC do estoque por valor."""
        df_calc = df.copy()
        df_calc["valor_estoque"] = df_calc["ESTOQUE"] * df_calc["VLRUNIT"]

        # Agrupar por produto
        valores = df_calc.groupby("CODPROD")["valor_estoque"].sum().reset_index()
        valores = valores.sort_values("valor_estoque", ascending=False)

        # Calcular percentual acumulado
        total = valores["valor_estoque"].sum()
        valores["percentual"] = valores["valor_estoque"] / total * 100
        valores["percentual_acum"] = valores["percentual"].cumsum()

        # Classificar ABC
        def classificar(pct_acum):
            if pct_acum <= 80:
                return "A"
            elif pct_acum <= 95:
                return "B"
            else:
                return "C"

        valores["classe"] = valores["percentual_acum"].apply(classificar)

        # Resumo por classe
        resumo = valores.groupby("classe").agg({
            "CODPROD": "count",
            "valor_estoque": "sum"
        }).reset_index()

        resumo.columns = ["classe", "qtd_produtos", "valor_estoque"]

        resultado = {}
        for _, row in resumo.iterrows():
            classe = row["classe"]
            resultado[f"classe_{classe}"] = {
                "qtd_produtos": int(row["qtd_produtos"]),
                "valor_estoque": float(row["valor_estoque"]),
                "valor_estoque_formatted": self._format_currency(row["valor_estoque"]),
                "percentual": float(row["valor_estoque"] / total * 100)
            }

        resultado["descricao"] = "Curva ABC: A=80% do valor, B=15%, C=5%"
        resultado["total_produtos"] = len(valores)
        resultado["valor_total"] = float(total)
        resultado["valor_total_formatted"] = self._format_currency(total)

        return resultado

    def _calc_giro_estoque(
        self,
        df_estoque: pd.DataFrame,
        df_vendas: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Calcula giro de estoque.

        Formula: Custo das Vendas / Estoque Medio
        """
        # Calcular custo das vendas (usando VLRUNIT se disponivel)
        if "VLRUNIT" not in df_vendas.columns:
            return {
                "valor": None,
                "descricao": "Coluna VLRUNIT nao disponivel em vendas"
            }

        custo_vendas = (df_vendas["QTDNEG"] * df_vendas["VLRUNIT"]).sum()

        # Calcular valor do estoque
        if "VLRUNIT" not in df_estoque.columns:
            return {
                "valor": None,
                "descricao": "Coluna VLRUNIT nao disponivel em estoque"
            }

        valor_estoque = (df_estoque["ESTOQUE"] * df_estoque["VLRUNIT"]).sum()

        giro = self._safe_divide(custo_vendas, valor_estoque)

        return {
            "valor": round(float(giro), 2),
            "custo_vendas": float(custo_vendas),
            "custo_vendas_formatted": self._format_currency(custo_vendas),
            "valor_estoque": float(valor_estoque),
            "valor_estoque_formatted": self._format_currency(valor_estoque),
            "descricao": "Giro de estoque (vezes que o estoque foi renovado)"
        }

    def _calc_divergencia_erp_wms(
        self,
        df_erp: pd.DataFrame,
        df_wms: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Calcula divergencia entre ERP (TGFEST) e WMS (TGWEST).
        """
        # Agrupar ERP por produto
        erp = df_erp.groupby("CODPROD")["ESTOQUE"].sum().reset_index()
        erp.columns = ["CODPROD", "estoque_erp"]

        # Agrupar WMS por produto
        if "QTDESTOQUE" in df_wms.columns:
            col_wms = "QTDESTOQUE"
        elif "ESTOQUE" in df_wms.columns:
            col_wms = "ESTOQUE"
        else:
            return {
                "valor": None,
                "descricao": "Coluna de estoque WMS nao encontrada"
            }

        wms = df_wms.groupby("CODPROD")[col_wms].sum().reset_index()
        wms.columns = ["CODPROD", "estoque_wms"]

        # Merge
        comparacao = pd.merge(erp, wms, on="CODPROD", how="outer").fillna(0)
        comparacao["diferenca"] = comparacao["estoque_erp"] - comparacao["estoque_wms"]
        comparacao["diferenca_abs"] = comparacao["diferenca"].abs()

        # Produtos com divergencia
        divergentes = comparacao[comparacao["diferenca_abs"] > 0]
        divergentes = divergentes.sort_values("diferenca_abs", ascending=False)

        # Top 10 maiores divergencias
        top = divergentes.head(10).to_dict(orient="records")

        # Resumo
        total_divergencia = divergentes["diferenca_abs"].sum()
        qtd_divergentes = len(divergentes)

        return {
            "qtd_produtos_divergentes": qtd_divergentes,
            "total_divergencia_unidades": float(total_divergencia),
            "maiores_divergencias": top,
            "total_produtos_analisados": len(comparacao),
            "descricao": "Diferenca entre estoque ERP (TGFEST) e WMS (TGWEST)"
        }
