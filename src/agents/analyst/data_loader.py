# -*- coding: utf-8 -*-
"""
Data Loader do Agente Analista

Carrega dados com estrategia de fallback:
1. Tenta Data Lake local (Parquet) - mais rapido
2. Se falhar, tenta API Sankhya - dados mais frescos

Exemplo de uso:
    loader = AnalystDataLoader()

    # Carregar vendas do ultimo mes
    df = loader.load("vendas", data_inicio="2026-01-01", data_fim="2026-01-31")

    # Carregar estoque atual
    df = loader.load("estoque")
"""

import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, Union

import pandas as pd

from .config import DATA_SOURCES, ENTITY_TABLES

logger = logging.getLogger(__name__)


class AnalystDataLoader:
    """
    Carrega dados para o Agente Analista.

    Implementa estrategia de fallback:
    - Primeiro tenta carregar do Data Lake (local/Azure)
    - Se nao encontrar ou falhar, usa API Sankhya
    """

    def __init__(self):
        """Inicializa o loader."""
        self._sankhya_client = None
        self._cache: Dict[str, pd.DataFrame] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

    @property
    def sankhya_client(self):
        """Retorna cliente Sankhya, criando se necessario (lazy)."""
        if self._sankhya_client is None:
            from src.utils.sankhya_client import SankhyaClient
            self._sankhya_client = SankhyaClient()
        return self._sankhya_client

    def load(
        self,
        entity: str,
        data_inicio: Optional[Union[str, date]] = None,
        data_fim: Optional[Union[str, date]] = None,
        use_cache: bool = True,
        force_source: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Carrega dados de uma entidade.

        Args:
            entity: Nome da entidade (vendas, compras, estoque, empenho)
            data_inicio: Data inicial para filtro (YYYY-MM-DD ou date)
            data_fim: Data final para filtro (YYYY-MM-DD ou date)
            use_cache: Se True, usa cache em memoria
            force_source: Forcar fonte especifica ('datalake' ou 'sankhya')
            **kwargs: Filtros adicionais

        Returns:
            DataFrame com os dados
        """
        # Verificar cache
        cache_key = self._get_cache_key(entity, data_inicio, data_fim, kwargs)
        if use_cache and cache_key in self._cache:
            if self._is_cache_valid(cache_key):
                logger.debug(f"[{entity}] Usando dados do cache")
                return self._cache[cache_key].copy()

        # Converter datas
        if isinstance(data_inicio, date):
            data_inicio = data_inicio.strftime("%Y-%m-%d")
        if isinstance(data_fim, date):
            data_fim = data_fim.strftime("%Y-%m-%d")

        df = pd.DataFrame()

        # Estrategia de carregamento
        if force_source == "sankhya":
            df = self._load_from_sankhya(entity, data_inicio, data_fim, **kwargs)
        elif force_source == "datalake":
            df = self._load_from_datalake(entity, data_inicio, data_fim, **kwargs)
        else:
            # Fallback: Data Lake -> Sankhya
            df = self._load_with_fallback(entity, data_inicio, data_fim, **kwargs)

        # Atualizar cache
        if use_cache and not df.empty:
            self._cache[cache_key] = df.copy()
            self._cache_timestamps[cache_key] = datetime.now()

        return df

    def _load_with_fallback(
        self,
        entity: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Carrega com fallback: Data Lake -> Sankhya."""
        # 1. Tentar Data Lake primeiro
        try:
            df = self._load_from_datalake(entity, data_inicio, data_fim, **kwargs)
            if not df.empty:
                logger.info(f"[{entity}] Carregado do Data Lake: {len(df)} registros")
                return df
        except Exception as e:
            logger.warning(f"[{entity}] Data Lake indisponivel: {e}")

        # 2. Fallback para API Sankhya
        try:
            df = self._load_from_sankhya(entity, data_inicio, data_fim, **kwargs)
            if not df.empty:
                logger.info(f"[{entity}] Carregado da API Sankhya: {len(df)} registros")
                return df
        except Exception as e:
            logger.error(f"[{entity}] Erro ao carregar da API: {e}")

        logger.warning(f"[{entity}] Nenhuma fonte de dados disponivel")
        return pd.DataFrame()

    def _load_from_datalake(
        self,
        entity: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Carrega dados do Data Lake (arquivos Parquet locais)."""
        config = DATA_SOURCES["datalake"]
        local_path = config["local_path"] / entity

        if not local_path.exists():
            logger.debug(f"[{entity}] Diretorio nao existe: {local_path}")
            return pd.DataFrame()

        # Encontrar arquivos Parquet
        parquet_files = list(local_path.glob("*.parquet"))

        if not parquet_files:
            logger.debug(f"[{entity}] Nenhum arquivo Parquet encontrado")
            return pd.DataFrame()

        # Carregar todos os arquivos
        dfs = []
        for pf in parquet_files:
            try:
                df = pd.read_parquet(pf)
                dfs.append(df)
            except Exception as e:
                logger.warning(f"[{entity}] Erro ao ler {pf.name}: {e}")

        if not dfs:
            return pd.DataFrame()

        df = pd.concat(dfs, ignore_index=True)

        # Aplicar filtros de data se especificados
        df = self._apply_date_filter(df, data_inicio, data_fim)

        return df

    def _load_from_sankhya(
        self,
        entity: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Carrega dados diretamente da API Sankhya."""
        # Autenticar
        if not self.sankhya_client.autenticar():
            logger.error(f"[{entity}] Falha na autenticacao Sankhya")
            return pd.DataFrame()

        # Montar query
        query = self._build_query(entity, data_inicio, data_fim, **kwargs)

        if not query:
            logger.error(f"[{entity}] Entidade nao suportada para query direta")
            return pd.DataFrame()

        # Executar
        try:
            result = self.sankhya_client.executar_query(
                query,
                timeout=DATA_SOURCES["sankhya"]["timeout"]
            )
        except Exception as e:
            logger.error(f"[{entity}] Erro na execucao da query: {e}")
            return pd.DataFrame()

        if not result or not result.get("rows"):
            return pd.DataFrame()

        # Montar DataFrame
        columns = result.get("columns", [])
        rows = result.get("rows", [])

        if columns:
            df = pd.DataFrame(rows, columns=columns)
        else:
            df = pd.DataFrame(rows)

        return df

    def _build_query(
        self,
        entity: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """Monta query SQL para a entidade."""
        if entity not in ENTITY_TABLES:
            return None

        config = ENTITY_TABLES[entity]
        table = config["primary"]

        # Query base
        if entity == "vendas":
            query = """
                SELECT
                    c.NUNOTA, c.NUMNOTA, c.DTNEG, c.DTENTSAI,
                    c.CODPARC, c.CODEMP, c.CODVEND,
                    c.VLRNOTA, c.VLRDESCTOT, c.VLRFRETE,
                    i.CODPROD, i.QTDNEG, i.VLRUNIT, i.VLRTOT
                FROM TGFCAB c
                INNER JOIN TGFITE i ON c.NUNOTA = i.NUNOTA
                WHERE c.TIPMOV = 'V'
                  AND c.STATUSNOTA = 'L'
            """
        elif entity == "compras":
            query = """
                SELECT
                    c.NUNOTA, c.NUMNOTA, c.DTNEG, c.DTENTSAI,
                    c.CODPARC, c.CODEMP,
                    c.VLRNOTA, c.VLRDESCTOT, c.VLRFRETE,
                    i.CODPROD, i.QTDNEG, i.VLRUNIT, i.VLRTOT
                FROM TGFCAB c
                INNER JOIN TGFITE i ON c.NUNOTA = i.NUNOTA
                WHERE c.TIPMOV = 'C'
            """
        elif entity == "estoque":
            query = """
                SELECT
                    e.CODEMP, e.CODPROD, e.CODLOCAL, e.CONTROLE,
                    e.ESTOQUE, e.RESERVADO,
                    (e.ESTOQUE - NVL(e.RESERVADO, 0)) as DISPONIVEL,
                    p.DESCRPROD, p.REFERENCIA
                FROM TGFEST e
                INNER JOIN TGFPRO p ON e.CODPROD = p.CODPROD
                WHERE e.ESTOQUE > 0 OR e.RESERVADO > 0
            """
        else:
            return None

        # Adicionar filtro de data
        if data_inicio and entity in ["vendas", "compras"]:
            query += f" AND c.DTNEG >= TO_DATE('{data_inicio}', 'YYYY-MM-DD')"
        if data_fim and entity in ["vendas", "compras"]:
            query += f" AND c.DTNEG <= TO_DATE('{data_fim}', 'YYYY-MM-DD')"

        return query

    def _apply_date_filter(
        self,
        df: pd.DataFrame,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> pd.DataFrame:
        """Aplica filtro de data no DataFrame."""
        if df.empty:
            return df

        # Detectar coluna de data
        date_cols = ["DTNEG", "DATA", "DT_NEGOCIACAO", "data_negociacao"]
        date_col = None

        for col in date_cols:
            if col in df.columns:
                date_col = col
                break
            if col.lower() in [c.lower() for c in df.columns]:
                date_col = [c for c in df.columns if c.lower() == col.lower()][0]
                break

        if not date_col:
            return df

        # Converter para datetime
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        # Aplicar filtros
        if data_inicio:
            dt_inicio = pd.to_datetime(data_inicio)
            df = df[df[date_col] >= dt_inicio]

        if data_fim:
            dt_fim = pd.to_datetime(data_fim)
            df = df[df[date_col] <= dt_fim]

        return df

    def _get_cache_key(
        self,
        entity: str,
        data_inicio: Optional[str],
        data_fim: Optional[str],
        kwargs: Dict
    ) -> str:
        """Gera chave unica para o cache."""
        parts = [entity, str(data_inicio), str(data_fim)]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}={v}")
        return "_".join(parts)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se o cache ainda e valido."""
        if cache_key not in self._cache_timestamps:
            return False

        from .config import ANALYST_CONFIG
        ttl = ANALYST_CONFIG.get("cache_ttl", 300)

        elapsed = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return elapsed < ttl

    def clear_cache(self, entity: Optional[str] = None) -> None:
        """Limpa o cache."""
        if entity:
            keys_to_remove = [k for k in self._cache if k.startswith(entity)]
            for k in keys_to_remove:
                del self._cache[k]
                if k in self._cache_timestamps:
                    del self._cache_timestamps[k]
            logger.info(f"Cache limpo para: {entity}")
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info("Cache completamente limpo")

    def get_available_entities(self) -> list:
        """Retorna lista de entidades disponiveis."""
        return list(ENTITY_TABLES.keys())
