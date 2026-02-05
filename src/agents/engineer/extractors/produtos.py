# -*- coding: utf-8 -*-
"""
Extractor de Produtos (TGFPRO)

Extrai dados de produtos do Sankhya.
"""

from typing import Optional, List

from .base import BaseExtractor


class ProdutosExtractor(BaseExtractor):
    """Extrai dados de produtos do Sankhya."""

    def get_entity_name(self) -> str:
        return "produtos"

    def get_columns(self) -> List[str]:
        return [
            "CODPROD",
            "DESCRPROD",
            "COMPLDESC",
            "REFERENCIA",
            "MARCA",
            "CODGRUPOPROD",
            "DESCRGRUPOPROD",
            "ATIVO",
            "USOPROD",
            "ORIGPROD",
            "NCM",
            "CODVOL",
            "PESOBRUTO",
            "PESOLIQ",
            "LARGURA",
            "ALTURA",
            "ESPESSURA",
            "DTALTER"
        ]

    def get_query(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        apenas_ativos: bool = True,
        codgrupoprod: Optional[int] = None,
        id_range: Optional[tuple] = None,
        **kwargs
    ) -> str:
        """
        Query para extração de produtos.

        Args:
            data_inicio: Data inicial de alteração (YYYY-MM-DD)
            data_fim: Data final de alteração (YYYY-MM-DD)
            apenas_ativos: Filtrar apenas ativos (default: True)
            codgrupoprod: Código do grupo de produtos
            id_range: Tupla (coluna, inicio, fim) para extração por faixas
        """
        query = """
        SELECT
            p.CODPROD,
            p.DESCRPROD,
            p.COMPLDESC,
            p.REFERENCIA,
            p.MARCA,
            p.CODGRUPOPROD,
            g.DESCRGRUPOPROD,
            p.ATIVO,
            p.USOPROD,
            p.ORIGPROD,
            p.NCM,
            p.CODVOL,
            p.PESOBRUTO,
            p.PESOLIQ,
            p.LARGURA,
            p.ALTURA,
            p.ESPESSURA,
            p.DTALTER
        FROM TGFPRO p
        LEFT JOIN TGFGRU g ON g.CODGRUPOPROD = p.CODGRUPOPROD
        WHERE 1=1
        """

        # Filtro por faixa de ID
        if id_range:
            col, start, end = id_range
            query += f"\n  AND {col} >= {start} AND {col} < {end}"

        if data_inicio:
            query += f"\n  AND p.DTALTER >= TO_DATE('{data_inicio}', 'YYYY-MM-DD')"

        if data_fim:
            query += f"\n  AND p.DTALTER <= TO_DATE('{data_fim}', 'YYYY-MM-DD')"

        if apenas_ativos:
            query += "\n  AND p.ATIVO = 'S'"

        if codgrupoprod:
            query += f"\n  AND p.CODGRUPOPROD = {codgrupoprod}"

        query += "\nORDER BY p.CODPROD"

        return query
