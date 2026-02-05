# -*- coding: utf-8 -*-
"""
Extractor de Compras (TGFCAB + TGFITE)

Extrai dados de compras do Sankhya, incluindo cabecalho e itens.
Diferente de vendas, usa TIPMOV = 'C' (ou 'O' para pedidos).
"""

from typing import Optional, List

from .base import BaseExtractor


class ComprasExtractor(BaseExtractor):
    """
    Extrai dados de compras do Sankhya.

    Tipos de movimento:
    - 'C': Compra (nota fiscal de entrada)
    - 'O': Pedido de compra (ordem de compra)

    Exemplo de uso:
        extractor = ComprasExtractor()

        # Compras realizadas (notas fiscais)
        df = extractor.extract(data_inicio="2026-01-01", tipo_mov="C")

        # Pedidos de compra
        df = extractor.extract(data_inicio="2026-01-01", tipo_mov="O")
    """

    def get_entity_name(self) -> str:
        return "compras"

    def get_columns(self) -> List[str]:
        return [
            # Cabecalho
            "NUNOTA",
            "NUMNOTA",
            "CODEMP",
            "CODPARC",
            "NOMEPARC",  # Fornecedor
            "DTNEG",
            "DTENTSAI",  # Data de entrada/saida
            "DTFATUR",
            "VLRNOTA",
            "PENDENTE",
            "STATUSNOTA",
            "TIPMOV",
            "CODTIPOPER",
            "DESCROPER",
            "CODCOMPRADOR",
            "NOMECOMPRADOR",
            # Item
            "SEQUENCIA",
            "CODPROD",
            "DESCRPROD",
            "QTDNEG",
            "QTDENTREGUE",  # Quantidade ja entregue
            "VLRUNIT",
            "VLRTOT",
            "VLRDESC",
            "CODLOCALDESTINO",
            "CONTROLE",
            "REFERENCIA"
        ]

    def get_query(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        codemp: Optional[int] = None,
        codparc: Optional[int] = None,
        tipo_mov: str = "C",
        apenas_pendentes: bool = False,
        id_range: Optional[tuple] = None,
        **kwargs
    ) -> str:
        """
        Query para extracao de compras.

        Args:
            data_inicio: Data inicial (YYYY-MM-DD)
            data_fim: Data final (YYYY-MM-DD)
            codemp: Codigo da empresa (filtro opcional)
            codparc: Codigo do fornecedor (filtro opcional)
            tipo_mov: 'C' para compras, 'O' para pedidos (default: 'C')
            apenas_pendentes: Se True, retorna apenas itens pendentes
            id_range: Tupla (coluna, inicio, fim) para extracao por faixas
        """
        query = """
        SELECT
            c.NUNOTA,
            c.NUMNOTA,
            c.CODEMP,
            c.CODPARC,
            f.NOMEPARC,
            c.DTNEG,
            c.DTENTSAI,
            c.DTFATUR,
            c.VLRNOTA,
            c.PENDENTE,
            c.STATUSNOTA,
            c.TIPMOV,
            c.CODTIPOPER,
            t.DESCROPER,
            c.CODCOMPRADOR,
            comp.NOMEPARC AS NOMECOMPRADOR,
            i.SEQUENCIA,
            i.CODPROD,
            pr.DESCRPROD,
            i.QTDNEG,
            i.QTDENTREGUE,
            i.VLRUNIT,
            i.VLRTOT,
            i.VLRDESC,
            i.CODLOCALDESTINO,
            i.CONTROLE,
            pr.REFERENCIA
        FROM TGFCAB c
        INNER JOIN TGFITE i ON i.NUNOTA = c.NUNOTA
        LEFT JOIN TGFPAR f ON f.CODPARC = c.CODPARC
        LEFT JOIN TGFPAR comp ON comp.CODPARC = c.CODCOMPRADOR
        LEFT JOIN TGFPRO pr ON pr.CODPROD = i.CODPROD
        LEFT JOIN (
            SELECT CODTIPOPER, DESCROPER,
                   ROW_NUMBER() OVER (PARTITION BY CODTIPOPER ORDER BY DHALTER DESC) AS RN
            FROM TGFTOP
        ) t ON t.CODTIPOPER = c.CODTIPOPER AND t.RN = 1
        WHERE c.TIPMOV = '{tipo_mov}'
        """.format(tipo_mov=tipo_mov)

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

        if apenas_pendentes:
            query += "\n  AND i.PENDENTE = 'S'"

        query += "\nORDER BY c.DTNEG DESC, c.NUNOTA, i.SEQUENCIA"

        return query


class PedidosCompraExtractor(ComprasExtractor):
    """
    Extractor especifico para Pedidos de Compra (TIPMOV = 'O').

    Herda de ComprasExtractor mas com tipo_mov padrao 'O'.
    """

    def get_entity_name(self) -> str:
        return "pedidos_compra"

    def get_query(self, tipo_mov: str = "O", **kwargs) -> str:
        """Query para pedidos de compra (TIPMOV = 'O')."""
        return super().get_query(tipo_mov="O", **kwargs)
