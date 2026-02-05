# -*- coding: utf-8 -*-
"""
Extractor de Estoque (TGFEST)

Extrai posição de estoque do Sankhya.
"""

from typing import Optional, List

from .base import BaseExtractor


class EstoqueExtractor(BaseExtractor):
    """Extrai dados de estoque do Sankhya."""

    def get_entity_name(self) -> str:
        return "estoque"

    def get_columns(self) -> List[str]:
        return [
            "CODEMP",
            "CODPROD",
            "DESCRPROD",
            "CODLOCAL",
            "CODLOCAL_DESCR",
            "CONTROLE",
            "ESTOQUE",
            "RESERVADO",
            "DISPONIVEL"
        ]

    def get_query(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        codemp: int = 1,
        codlocal: Optional[int] = None,
        apenas_com_estoque: bool = True,
        id_range: Optional[tuple] = None,
        **kwargs
    ) -> str:
        """
        Query para extração de estoque.

        Args:
            data_inicio: Não utilizado (estoque é posição atual)
            data_fim: Não utilizado (estoque é posição atual)
            codemp: Código da empresa (default: 1)
            codlocal: Código do local (filtro opcional)
            apenas_com_estoque: Filtrar apenas produtos com estoque > 0
            id_range: Tupla (coluna, inicio, fim) para extração por faixas
        """
        query = f"""
        SELECT
            e.CODEMP,
            e.CODPROD,
            p.DESCRPROD,
            e.CODLOCAL,
            l.DESCRLOCAL AS CODLOCAL_DESCR,
            e.CONTROLE,
            NVL(e.ESTOQUE, 0) AS ESTOQUE,
            NVL(e.RESERVADO, 0) AS RESERVADO,
            NVL(e.ESTOQUE, 0) - NVL(e.RESERVADO, 0) AS DISPONIVEL
        FROM TGFEST e
        LEFT JOIN TGFPRO p ON p.CODPROD = e.CODPROD
        LEFT JOIN TGFLOC l ON l.CODLOCAL = e.CODLOCAL
        WHERE e.CODEMP = {codemp}
        """

        # Filtro por faixa de ID
        if id_range:
            col, start, end = id_range
            query += f"\n  AND {col} >= {start} AND {col} < {end}"

        if codlocal:
            query += f"\n  AND e.CODLOCAL = {codlocal}"

        if apenas_com_estoque:
            query += "\n  AND NVL(e.ESTOQUE, 0) > 0"

        query += "\nORDER BY e.CODPROD, e.CODLOCAL, e.CONTROLE"

        return query
