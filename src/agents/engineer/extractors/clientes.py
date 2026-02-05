# -*- coding: utf-8 -*-
"""
Extractor de Clientes/Parceiros (TGFPAR)

Extrai dados de clientes, fornecedores e outros parceiros do Sankhya.
"""

from typing import Optional, List

from .base import BaseExtractor


class ClientesExtractor(BaseExtractor):
    """Extrai dados de clientes/parceiros do Sankhya."""

    def get_entity_name(self) -> str:
        return "clientes"

    def get_columns(self) -> List[str]:
        return [
            "CODPARC",
            "NOMEPARC",
            "RAZAOSOCIAL",
            "CGC_CPF",
            "IDENTINSCESTAD",
            "TIPPESSOA",
            "CLIENTE",
            "FORNECEDOR",
            "VENDEDOR",
            "TRANSPORTADORA",
            "ATIVO",
            "DTCAD",
            "DTALTER",
            "EMAIL",
            "TELEFONE",
            "CEP",
            "CODEND",
            "NUMEND",
            "COMPLEMENTO",
            "CODBAI",
            "NOMEBAI",
            "CODCID",
            "NOMECID",
            "UF",
            "CODVEND",
            "APELIDO_VEND",
            "LIMCRED"
        ]

    def get_query(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        apenas_clientes: bool = False,
        apenas_fornecedores: bool = False,
        apenas_ativos: bool = True,
        id_range: Optional[tuple] = None,
        **kwargs
    ) -> str:
        """
        Query para extração de parceiros.

        Args:
            data_inicio: Data inicial de cadastro (YYYY-MM-DD)
            data_fim: Data final de cadastro (YYYY-MM-DD)
            apenas_clientes: Filtrar apenas clientes
            apenas_fornecedores: Filtrar apenas fornecedores
            apenas_ativos: Filtrar apenas ativos (default: True)
            id_range: Tupla (coluna, inicio, fim) para extração por faixas
        """
        query = """
        SELECT
            p.CODPARC,
            p.NOMEPARC,
            p.RAZAOSOCIAL,
            p.CGC_CPF,
            p.IDENTINSCESTAD,
            p.TIPPESSOA,
            p.CLIENTE,
            p.FORNECEDOR,
            p.VENDEDOR,
            p.TRANSPORTADORA,
            p.ATIVO,
            p.DTCAD,
            p.DTALTER,
            p.EMAIL,
            p.TELEFONE,
            p.CEP,
            p.CODEND,
            p.NUMEND,
            p.COMPLEMENTO,
            p.CODBAI,
            b.NOMEBAI,
            p.CODCID,
            c.NOMECID,
            c.UF,
            p.CODVEND,
            v.APELIDO AS APELIDO_VEND,
            p.LIMCRED
        FROM TGFPAR p
        LEFT JOIN TSIBAI b ON b.CODBAI = p.CODBAI
        LEFT JOIN TSICID c ON c.CODCID = p.CODCID
        LEFT JOIN TGFVEN v ON v.CODVEND = p.CODVEND
        WHERE 1=1
        """

        # Filtro por faixa de ID (para extração em lotes)
        if id_range:
            col, start, end = id_range
            query += f"\n  AND {col} >= {start} AND {col} < {end}"

        if data_inicio:
            query += f"\n  AND p.DTCAD >= TO_DATE('{data_inicio}', 'YYYY-MM-DD')"

        if data_fim:
            query += f"\n  AND p.DTCAD <= TO_DATE('{data_fim}', 'YYYY-MM-DD')"

        if apenas_clientes:
            query += "\n  AND p.CLIENTE = 'S'"

        if apenas_fornecedores:
            query += "\n  AND p.FORNECEDOR = 'S'"

        if apenas_ativos:
            query += "\n  AND p.ATIVO = 'S'"

        query += "\nORDER BY p.CODPARC"

        return query
