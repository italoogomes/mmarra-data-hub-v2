# -*- coding: utf-8 -*-
"""
Data Mapper - Transformação e Mapeamento de Dados

Responsável por:
- Renomear colunas (de-para)
- Criar colunas calculadas
- Mapear códigos para descrições
- Preparar dados para star schema (dimensões e fatos)
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


class DataMapper:
    """
    Mapeia e transforma dados para o modelo de destino.

    Exemplo de uso:
        mapper = DataMapper()
        df_mapeado = mapper.map(df, entity="clientes")
    """

    # Mapeamento de colunas: origem -> destino
    COLUMN_MAPPING = {
        "clientes": {
            "CODPARC": "cod_parceiro",
            "NOMEPARC": "nome_fantasia",
            "RAZAOSOCIAL": "razao_social",
            "CGC_CPF": "documento",
            "TIPPESSOA": "tipo_pessoa",
            "CLIENTE": "is_cliente",
            "FORNECEDOR": "is_fornecedor",
            "ATIVO": "is_ativo",
            "EMAIL": "email",
            "TELEFONE": "telefone",
            "CEP": "cep",
            "NOMECID": "cidade",
            "UF": "uf",
            "CODVEND": "cod_vendedor",
            "APELIDO_VEND": "nome_vendedor",
            "LIMCRED": "limite_credito"
        },
        "vendas": {
            "NUNOTA": "id_nota",
            "NUMNOTA": "numero_nota",
            "CODEMP": "cod_empresa",
            "CODPARC": "cod_parceiro",
            "NOMEPARC": "nome_parceiro",
            "DTNEG": "data_negociacao",
            "DTFATUR": "data_faturamento",
            "VLRNOTA": "valor_nota",
            "CODVEND": "cod_vendedor",
            "APELIDO_VEND": "nome_vendedor",
            "SEQUENCIA": "sequencia_item",
            "CODPROD": "cod_produto",
            "DESCRPROD": "nome_produto",
            "QTDNEG": "quantidade",
            "VLRUNIT": "valor_unitario",
            "VLRTOT": "valor_total",
            "VLRDESC": "valor_desconto"
        },
        "produtos": {
            "CODPROD": "cod_produto",
            "DESCRPROD": "nome_produto",
            "COMPLDESC": "descricao_complementar",
            "REFERENCIA": "referencia",
            "MARCA": "marca",
            "CODGRUPOPROD": "cod_grupo",
            "DESCRGRUPOPROD": "nome_grupo",
            "ATIVO": "is_ativo",
            "NCM": "ncm",
            "CODVOL": "unidade_medida",
            "PESOBRUTO": "peso_bruto",
            "PESOLIQ": "peso_liquido"
        },
        "estoque": {
            "CODEMP": "cod_empresa",
            "CODPROD": "cod_produto",
            "DESCRPROD": "nome_produto",
            "CODLOCAL": "cod_local",
            "CODLOCAL_DESCR": "nome_local",
            "CONTROLE": "lote",
            "ESTOQUE": "quantidade_estoque",
            "RESERVADO": "quantidade_reservada",
            "DISPONIVEL": "quantidade_disponivel"
        },
        "vendedores": {
            "CODVEND": "cod_vendedor",
            "APELIDO": "nome",
            "ATIVO": "is_ativo",
            "TIPVEND": "tipo",
            "EMAIL": "email",
            "CODGER": "cod_gerente"
        }
    }

    # Mapeamento de valores (códigos para descrições)
    VALUE_MAPPING = {
        "tipo_pessoa": {
            "J": "Jurídica",
            "F": "Física"
        },
        "tipo_vendedor": {
            "V": "Vendedor",
            "C": "Comprador",
            "R": "Representante"
        },
        "boolean": {
            "S": True,
            "N": False
        }
    }

    def __init__(self):
        """Inicializa o mapper."""
        self.stats = {}

    def map(
        self,
        df: pd.DataFrame,
        entity: str,
        rename_columns: bool = True,
        map_values: bool = True,
        add_calculated: bool = True
    ) -> pd.DataFrame:
        """
        Mapeia e transforma um DataFrame.

        Args:
            df: DataFrame a mapear
            entity: Nome da entidade (clientes, vendas, etc)
            rename_columns: Renomear colunas para padrão destino
            map_values: Mapear valores codificados para descrições
            add_calculated: Adicionar colunas calculadas

        Returns:
            DataFrame mapeado
        """
        if df.empty:
            logger.warning(f"[{entity}] DataFrame vazio, nada a mapear")
            return df

        logger.info(f"[{entity}] Iniciando mapeamento de {len(df)} registros...")

        # 1. Adicionar colunas calculadas
        if add_calculated:
            df = self._add_calculated_columns(df, entity)

        # 2. Mapear valores
        if map_values:
            df = self._map_values(df, entity)

        # 3. Renomear colunas
        if rename_columns:
            df = self._rename_columns(df, entity)

        self.stats[entity] = {
            "records": len(df),
            "columns": len(df.columns),
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"[{entity}] Mapeamento concluído: {len(df.columns)} colunas")

        return df

    def _rename_columns(
        self,
        df: pd.DataFrame,
        entity: str
    ) -> pd.DataFrame:
        """Renomeia colunas conforme mapeamento."""
        mapping = self.COLUMN_MAPPING.get(entity, {})

        if not mapping:
            return df

        # Filtrar apenas colunas que existem
        rename_dict = {k: v for k, v in mapping.items() if k in df.columns}

        if rename_dict:
            df = df.rename(columns=rename_dict)

        return df

    def _map_values(
        self,
        df: pd.DataFrame,
        entity: str
    ) -> pd.DataFrame:
        """Mapeia valores codificados para descrições."""
        # Mapear tipo pessoa
        if "TIPPESSOA" in df.columns:
            df["TIPPESSOA"] = df["TIPPESSOA"].map(
                self.VALUE_MAPPING["tipo_pessoa"]
            ).fillna(df["TIPPESSOA"])

        # Mapear tipo vendedor
        if "TIPVEND" in df.columns:
            df["TIPVEND"] = df["TIPVEND"].map(
                self.VALUE_MAPPING["tipo_vendedor"]
            ).fillna(df["TIPVEND"])

        # Mapear booleanos (S/N -> True/False)
        boolean_cols = ["ATIVO", "CLIENTE", "FORNECEDOR", "PENDENTE"]
        for col in boolean_cols:
            if col in df.columns:
                df[col] = df[col].map(self.VALUE_MAPPING["boolean"]).fillna(False)

        return df

    def _add_calculated_columns(
        self,
        df: pd.DataFrame,
        entity: str
    ) -> pd.DataFrame:
        """Adiciona colunas calculadas."""
        if entity == "vendas":
            # Valor líquido (total - desconto)
            if "VLRTOT" in df.columns and "VLRDESC" in df.columns:
                df["VLRLIQ"] = df["VLRTOT"] - df["VLRDESC"].fillna(0)

            # Margem percentual de desconto
            if "VLRTOT" in df.columns and "VLRDESC" in df.columns:
                df["PERC_DESC"] = (df["VLRDESC"].fillna(0) / df["VLRTOT"].replace(0, 1)) * 100

        elif entity == "estoque":
            # Percentual reservado
            if "ESTOQUE" in df.columns and "RESERVADO" in df.columns:
                df["PERC_RESERVADO"] = (
                    df["RESERVADO"].fillna(0) / df["ESTOQUE"].replace(0, 1)
                ) * 100

        elif entity == "clientes":
            # Flag pessoa jurídica
            if "TIPPESSOA" in df.columns:
                df["IS_PJ"] = df["TIPPESSOA"] == "J"

        return df

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de mapeamento."""
        return self.stats

    def to_dimension(
        self,
        df: pd.DataFrame,
        entity: str,
        key_column: str
    ) -> pd.DataFrame:
        """
        Prepara DataFrame como dimensão (deduplicado pela chave).

        Args:
            df: DataFrame fonte
            entity: Nome da entidade
            key_column: Coluna chave da dimensão

        Returns:
            DataFrame dimensão
        """
        if key_column not in df.columns:
            logger.error(f"Coluna chave '{key_column}' não encontrada")
            return df

        # Deduplicar mantendo o registro mais recente
        df = df.drop_duplicates(subset=[key_column], keep="last")

        # Adicionar surrogate key
        df = df.reset_index(drop=True)
        df["sk_" + entity] = df.index + 1

        return df

    def to_fact(
        self,
        df: pd.DataFrame,
        entity: str,
        measure_columns: List[str],
        dimension_keys: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Prepara DataFrame como fato (com chaves de dimensão).

        Args:
            df: DataFrame fonte
            entity: Nome da entidade
            measure_columns: Colunas de medidas (valores numéricos)
            dimension_keys: Dict {coluna_fato: coluna_dimensao}

        Returns:
            DataFrame fato
        """
        # Selecionar apenas colunas relevantes
        cols = list(dimension_keys.keys()) + measure_columns

        # Filtrar colunas que existem
        cols = [c for c in cols if c in df.columns]

        df = df[cols].copy()

        # Adicionar data de carga
        df["dt_carga"] = datetime.now()

        return df
