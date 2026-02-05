# -*- coding: utf-8 -*-
"""
Extractor de Vendas (TGFCAB + TGFITE)

Extrai dados de vendas do Sankhya, incluindo cabeçalho e itens.
"""

from typing import Optional, List

from .base import BaseExtractor


class VendasExtractor(BaseExtractor):
    """Extrai dados de vendas do Sankhya."""

    def get_entity_name(self) -> str:
        return "vendas"

    def get_columns(self) -> List[str]:
        return [
            # Cabeçalho
            "NUNOTA",
            "NUMNOTA",
            "CODEMP",
            "CODPARC",
            "NOMEPARC",
            "DTNEG",
            "DTFATUR",
            "VLRNOTA",
            "PENDENTE",
            "STATUSNOTA",
            "TIPMOV",
            "CODTIPOPER",
            "DESCROPER",
            "CODVEND",
            "APELIDO_VEND",
            "CODCENCUS",
            # Item
            "SEQUENCIA",
            "CODPROD",
            "DESCRPROD",
            "QTDNEG",
            "VLRUNIT",
            "VLRTOT",
            "VLRDESC",
            "CODLOCALORIG",
            "CONTROLE",
            "REFERENCIA"
        ]

    def get_query(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        codemp: Optional[int] = None,
        codparc: Optional[int] = None,
        id_range: Optional[tuple] = None,
        **kwargs
    ) -> str:
        """
        Query para extração de vendas.

        Args:
            data_inicio: Data inicial (YYYY-MM-DD)
            data_fim: Data final (YYYY-MM-DD)
            codemp: Código da empresa (filtro opcional)
            codparc: Código do parceiro (filtro opcional)
            id_range: Tupla (coluna, inicio, fim) para extração por faixas
        """
        query = """
        SELECT
            c.NUNOTA,
            c.NUMNOTA,
            c.CODEMP,
            c.CODPARC,
            p.NOMEPARC,
            c.DTNEG,
            c.DTFATUR,
            c.VLRNOTA,
            c.PENDENTE,
            c.STATUSNOTA,
            c.TIPMOV,
            c.CODTIPOPER,
            t.DESCROPER,
            c.CODVEND,
            v.APELIDO AS APELIDO_VEND,
            c.CODCENCUS,
            i.SEQUENCIA,
            i.CODPROD,
            pr.DESCRPROD,
            i.QTDNEG,
            i.VLRUNIT,
            i.VLRTOT,
            i.VLRDESC,
            i.CODLOCALORIG,
            i.CONTROLE,
            pr.REFERENCIA
        FROM TGFCAB c
        INNER JOIN TGFITE i ON i.NUNOTA = c.NUNOTA
        LEFT JOIN TGFPAR p ON p.CODPARC = c.CODPARC
        LEFT JOIN TGFPRO pr ON pr.CODPROD = i.CODPROD
        LEFT JOIN TGFVEN v ON v.CODVEND = c.CODVEND
        LEFT JOIN (
            SELECT CODTIPOPER, DESCROPER,
                   ROW_NUMBER() OVER (PARTITION BY CODTIPOPER ORDER BY DHALTER DESC) AS RN
            FROM TGFTOP
        ) t ON t.CODTIPOPER = c.CODTIPOPER AND t.RN = 1
        WHERE c.TIPMOV = 'V'
        """

        # Filtro por faixa de ID
        if id_range:
            col, start, end = id_range
            query += f"\n  AND {col} >= {start} AND {col} < {end}"

        if data_inicio:
            query += f"\n  AND c.DTNEG >= TO_DATE('{data_inicio}', 'YYYY-MM-DD')"

        if data_fim:
            query += f"\n  AND c.DTNEG <= TO_DATE('{data_fim}', 'YYYY-MM-DD')"

        if codemp:
            query += f"\n  AND c.CODEMP = {codemp}"

        if codparc:
            query += f"\n  AND c.CODPARC = {codparc}"

        query += "\nORDER BY c.DTNEG DESC, c.NUNOTA, i.SEQUENCIA"

        return query
