# -*- coding: utf-8 -*-
"""
Data Cleaner - Limpeza e Validação de Dados

Responsável por:
- Remover duplicatas
- Tratar valores nulos
- Validar tipos de dados
- Normalizar strings
- Validar regras de negócio
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Limpa e valida dados extraídos.

    Exemplo de uso:
        cleaner = DataCleaner()
        df_limpo = cleaner.clean(df, entity="clientes")
    """

    # Configurações de limpeza por entidade
    ENTITY_CONFIG = {
        "clientes": {
            "primary_key": ["CODPARC"],
            "required_fields": ["CODPARC", "NOMEPARC"],
            "string_fields": ["NOMEPARC", "RAZAOSOCIAL", "CGC_CPF", "EMAIL", "TELEFONE"],
            "numeric_fields": ["CODPARC", "CODVEND", "LIMCRED"],
            "date_fields": ["DTCAD", "DTALTER"],
            "boolean_fields": {"ATIVO": "S", "CLIENTE": "S", "FORNECEDOR": "S"}
        },
        "vendas": {
            "primary_key": ["NUNOTA", "SEQUENCIA"],
            "required_fields": ["NUNOTA", "CODPROD", "QTDNEG"],
            "string_fields": ["NOMEPARC", "DESCRPROD"],
            "numeric_fields": ["NUNOTA", "CODPARC", "CODPROD", "QTDNEG", "VLRUNIT", "VLRTOT"],
            "date_fields": ["DTNEG", "DTFATUR"],
            "boolean_fields": {"PENDENTE": "S"}
        },
        "produtos": {
            "primary_key": ["CODPROD"],
            "required_fields": ["CODPROD", "DESCRPROD"],
            "string_fields": ["DESCRPROD", "COMPLDESC", "REFERENCIA", "MARCA", "NCM"],
            "numeric_fields": ["CODPROD", "CODGRUPOPROD", "PESOBRUTO", "PESOLIQ"],
            "date_fields": ["DTALTER"],
            "boolean_fields": {"ATIVO": "S"}
        },
        "estoque": {
            "primary_key": ["CODEMP", "CODPROD", "CODLOCAL", "CONTROLE"],
            "required_fields": ["CODPROD", "ESTOQUE"],
            "string_fields": ["DESCRPROD", "CONTROLE"],
            "numeric_fields": ["CODEMP", "CODPROD", "CODLOCAL", "ESTOQUE", "RESERVADO", "DISPONIVEL"],
            "date_fields": [],
            "boolean_fields": {}
        },
        "vendedores": {
            "primary_key": ["CODVEND"],
            "required_fields": ["CODVEND", "APELIDO"],
            "string_fields": ["APELIDO", "EMAIL", "TIPVEND"],
            "numeric_fields": ["CODVEND", "CODGER"],
            "date_fields": [],
            "boolean_fields": {"ATIVO": "S"}
        }
    }

    def __init__(self):
        """Inicializa o cleaner."""
        self.stats = {}

    def clean(
        self,
        df: pd.DataFrame,
        entity: str,
        remove_duplicates: bool = True,
        fill_nulls: bool = True,
        validate_types: bool = True,
        normalize_strings: bool = True
    ) -> pd.DataFrame:
        """
        Limpa um DataFrame.

        Args:
            df: DataFrame a limpar
            entity: Nome da entidade (clientes, vendas, etc)
            remove_duplicates: Remover registros duplicados
            fill_nulls: Preencher valores nulos
            validate_types: Validar e converter tipos
            normalize_strings: Normalizar strings (trim, upper)

        Returns:
            DataFrame limpo
        """
        if df.empty:
            logger.warning(f"[{entity}] DataFrame vazio, nada a limpar")
            return df

        original_count = len(df)
        config = self.ENTITY_CONFIG.get(entity, {})

        logger.info(f"[{entity}] Iniciando limpeza de {original_count} registros...")

        # 1. Remover duplicatas
        if remove_duplicates and config.get("primary_key"):
            df = self._remove_duplicates(df, config["primary_key"], entity)

        # 2. Normalizar strings
        if normalize_strings and config.get("string_fields"):
            df = self._normalize_strings(df, config["string_fields"], entity)

        # 3. Preencher nulos
        if fill_nulls:
            df = self._fill_nulls(df, config, entity)

        # 4. Validar tipos
        if validate_types:
            df = self._validate_types(df, config, entity)

        # 5. Adicionar metadados
        df = self._add_metadata(df, entity)

        final_count = len(df)
        removed = original_count - final_count

        self.stats[entity] = {
            "original": original_count,
            "final": final_count,
            "removed": removed,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"[{entity}] Limpeza concluída: {final_count} registros ({removed} removidos)")

        return df

    def _remove_duplicates(
        self,
        df: pd.DataFrame,
        primary_key: List[str],
        entity: str
    ) -> pd.DataFrame:
        """Remove registros duplicados baseado na chave primária."""
        # Verificar se todas as colunas da PK existem
        pk_cols = [col for col in primary_key if col in df.columns]

        if not pk_cols:
            return df

        before = len(df)
        df = df.drop_duplicates(subset=pk_cols, keep="last")
        after = len(df)

        if before != after:
            logger.debug(f"[{entity}] Removidas {before - after} duplicatas")

        return df

    def _normalize_strings(
        self,
        df: pd.DataFrame,
        string_fields: List[str],
        entity: str
    ) -> pd.DataFrame:
        """Normaliza campos string (trim, upper para alguns campos)."""
        for col in string_fields:
            if col not in df.columns:
                continue

            # Strip whitespace
            df[col] = df[col].astype(str).str.strip()

            # Substituir 'None' e 'nan' por vazio
            df[col] = df[col].replace(["None", "nan", "NaN", "null"], "")

        return df

    def _fill_nulls(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any],
        entity: str
    ) -> pd.DataFrame:
        """Preenche valores nulos com valores padrão."""
        # Numéricos: preencher com 0
        for col in config.get("numeric_fields", []):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Strings: preencher com vazio
        for col in config.get("string_fields", []):
            if col in df.columns:
                df[col] = df[col].fillna("")

        # Booleans: preencher com 'N'
        for col in config.get("boolean_fields", {}):
            if col in df.columns:
                df[col] = df[col].fillna("N")

        return df

    # Formatos de data conhecidos do Sankhya
    SANKHYA_DATE_FORMATS = [
        "%d%m%Y %H:%M:%S",    # 03022026 08:16:40 (formato padrao Sankhya)
        "%d%m%Y",              # 03022026
        "%Y-%m-%d %H:%M:%S",   # 2026-02-03 08:16:40 (ISO)
        "%Y-%m-%d",            # 2026-02-03
        "%d/%m/%Y %H:%M:%S",   # 03/02/2026 08:16:40
        "%d/%m/%Y",            # 03/02/2026
    ]

    def _validate_types(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any],
        entity: str
    ) -> pd.DataFrame:
        """Valida e converte tipos de dados."""
        # Converter numéricos
        for col in config.get("numeric_fields", []):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Converter datas (tentar múltiplos formatos do Sankhya)
        for col in config.get("date_fields", []):
            if col in df.columns:
                df[col] = self._parse_sankhya_date(df[col], col, entity)

        return df

    def _parse_sankhya_date(
        self,
        series: pd.Series,
        col_name: str,
        entity: str
    ) -> pd.Series:
        """
        Converte coluna de data tentando múltiplos formatos do Sankhya.

        O Sankhya retorna datas no formato DDMMYYYY HH:MM:SS que o pandas
        não reconhece automaticamente.
        """
        # Se já é datetime, retornar
        if pd.api.types.is_datetime64_any_dtype(series):
            return series

        # Contar valores não-nulos originais
        non_null_original = series.notna().sum()

        if non_null_original == 0:
            logger.warning(f"[{entity}] Coluna {col_name} está 100% nula")
            return pd.to_datetime(series, errors="coerce")

        # Tentar cada formato conhecido
        for fmt in self.SANKHYA_DATE_FORMATS:
            try:
                result = pd.to_datetime(series, format=fmt, errors="coerce")
                non_null_converted = result.notna().sum()

                # Se converteu pelo menos 80% dos valores, usar este formato
                if non_null_converted >= non_null_original * 0.8:
                    logger.debug(f"[{entity}] Coluna {col_name} convertida com formato {fmt}")
                    return result
            except Exception:
                continue

        # Fallback: tentar inferir automaticamente
        logger.warning(f"[{entity}] Coluna {col_name} - nenhum formato conhecido funcionou, tentando inferir...")
        return pd.to_datetime(series, errors="coerce")

    def _add_metadata(self, df: pd.DataFrame, entity: str) -> pd.DataFrame:
        """Adiciona colunas de metadados."""
        df["_extracted_at"] = datetime.now()
        df["_entity"] = entity
        return df

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de limpeza."""
        return self.stats

    def validate_required_fields(
        self,
        df: pd.DataFrame,
        entity: str
    ) -> pd.DataFrame:
        """
        Remove registros com campos obrigatórios nulos.

        Args:
            df: DataFrame a validar
            entity: Nome da entidade

        Returns:
            DataFrame apenas com registros válidos
        """
        config = self.ENTITY_CONFIG.get(entity, {})
        required = config.get("required_fields", [])

        if not required:
            return df

        # Verificar quais colunas existem
        required_cols = [col for col in required if col in df.columns]

        if not required_cols:
            return df

        before = len(df)
        df = df.dropna(subset=required_cols)
        after = len(df)

        if before != after:
            logger.warning(f"[{entity}] Removidos {before - after} registros com campos obrigatórios nulos")

        return df
