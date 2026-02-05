# -*- coding: utf-8 -*-
"""
Extractor de Vendedores/Compradores (TGFVEN)

Extrai dados de vendedores, compradores e representantes do Sankhya.
"""

from typing import Optional, List

from .base import BaseExtractor


class VendedoresExtractor(BaseExtractor):
    """Extrai dados de vendedores/compradores do Sankhya."""

    def get_entity_name(self) -> str:
        return "vendedores"

    def get_columns(self) -> List[str]:
        return [
            "CODVEND",
            "APELIDO",
            "ATIVO",
            "TIPVEND",
            "EMAIL",
            "CODGER"
        ]

    def get_query(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        apenas_ativos: bool = False,
        tipvend: Optional[str] = None,
        id_range: Optional[tuple] = None,
        **kwargs
    ) -> str:
        """
        Query para extração de vendedores/compradores.

        Args:
            data_inicio: Não utilizado (cadastro)
            data_fim: Não utilizado (cadastro)
            apenas_ativos: Filtrar apenas ativos
            tipvend: Tipo de vendedor (V=Vendedor, C=Comprador, R=Representante)
            id_range: Tupla (coluna, inicio, fim) para extração por faixas
        """
        query = """
        SELECT
            v.CODVEND,
            v.APELIDO,
            v.ATIVO,
            v.TIPVEND,
            v.EMAIL,
            v.CODGER
        FROM TGFVEN v
        WHERE 1=1
        """

        # Filtro por faixa de ID
        if id_range:
            col, start, end = id_range
            query += f"\n  AND {col} >= {start} AND {col} < {end}"

        if apenas_ativos:
            query += "\n  AND v.ATIVO = 'S'"

        if tipvend:
            query += f"\n  AND v.TIPVEND = '{tipvend}'"

        query += "\nORDER BY v.CODVEND"

        return query
