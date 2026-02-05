# -*- coding: utf-8 -*-
"""
Classe base para extractors do Agente Engenheiro

Define a interface padrão para todos os extractors.
Reutiliza o SankhyaClient de src/utils/.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd

from src.utils.sankhya_client import SankhyaClient

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """
    Classe base abstrata para extractors do Agente Engenheiro.

    Cada extractor deve implementar:
    - get_entity_name(): Nome da entidade (ex: 'vendas', 'clientes')
    - get_query(): Query SQL para extração
    - get_columns(): Lista de colunas esperadas

    Exemplo de uso:
        class VendasExtractor(BaseExtractor):
            def get_entity_name(self) -> str:
                return "vendas"

            def get_query(self, **kwargs) -> str:
                return "SELECT * FROM TGFCAB WHERE ..."

            def get_columns(self) -> List[str]:
                return ["NUNOTA", "DTNEG", ...]

        extractor = VendasExtractor()
        df = extractor.extract()
    """

    def __init__(self):
        """Inicializa o extractor com cliente Sankhya."""
        self._client: Optional[SankhyaClient] = None
        self._authenticated = False

    @property
    def client(self) -> SankhyaClient:
        """Retorna cliente Sankhya, criando se necessário."""
        if self._client is None:
            self._client = SankhyaClient()
        return self._client

    @abstractmethod
    def get_entity_name(self) -> str:
        """Retorna o nome da entidade (ex: 'vendas', 'clientes')."""
        pass

    @abstractmethod
    def get_query(self, **kwargs) -> str:
        """
        Retorna a query SQL para extração.

        Args:
            **kwargs: Parâmetros opcionais (data_inicio, data_fim, etc)

        Returns:
            Query SQL como string
        """
        pass

    @abstractmethod
    def get_columns(self) -> List[str]:
        """Retorna lista de nomes das colunas esperadas."""
        pass

    def _ensure_authenticated(self) -> bool:
        """Garante que o cliente está autenticado."""
        if not self._authenticated:
            self._authenticated = self.client.autenticar()
            if not self._authenticated:
                logger.error(f"[{self.get_entity_name()}] Falha na autenticação")
        return self._authenticated

    def extract(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrai dados do Sankhya.

        Args:
            data_inicio: Data inicial no formato YYYY-MM-DD
            data_fim: Data final no formato YYYY-MM-DD
            limit: Limite de registros (útil para testes)
            **kwargs: Parâmetros adicionais para a query

        Returns:
            DataFrame com os dados extraídos (vazio se erro)
        """
        entity = self.get_entity_name()
        columns = self.get_columns()

        logger.info(f"[{entity}] Iniciando extração...")

        # Autenticar
        if not self._ensure_authenticated():
            return pd.DataFrame(columns=columns)

        # Montar query
        query = self.get_query(
            data_inicio=data_inicio,
            data_fim=data_fim,
            **kwargs
        )

        # Adicionar limite se especificado
        if limit:
            query = f"SELECT * FROM ({query}) WHERE ROWNUM <= {limit}"

        logger.debug(f"[{entity}] Query: {query[:200]}...")

        # Executar
        try:
            result = self.client.executar_query(query, timeout=300)
        except Exception as e:
            logger.error(f"[{entity}] Erro na execução: {e}")
            return pd.DataFrame(columns=columns)

        if not result:
            logger.error(f"[{entity}] Resultado vazio ou erro na API")
            return pd.DataFrame(columns=columns)

        rows = result.get("rows", [])

        if not rows:
            logger.warning(f"[{entity}] Nenhum registro encontrado")
            return pd.DataFrame(columns=columns)

        # Criar DataFrame
        df = pd.DataFrame(rows, columns=columns)

        logger.info(f"[{entity}] Extraídos {len(df)} registros")

        return df

    def extract_by_range(
        self,
        id_column: str,
        id_max: int,
        range_size: int = 5000,
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrai dados em faixas para contornar limite da API (5000 registros).

        Args:
            id_column: Nome da coluna de ID para filtrar (ex: 'CODPROD')
            id_max: Valor máximo do ID
            range_size: Tamanho de cada faixa (default: 5000)
            **kwargs: Parâmetros adicionais para a query

        Returns:
            DataFrame consolidado com todos os dados
        """
        entity = self.get_entity_name()
        columns = self.get_columns()

        logger.info(f"[{entity}] Extração por faixas (0 a {id_max}, step {range_size})")

        if not self._ensure_authenticated():
            return pd.DataFrame(columns=columns)

        all_dfs = []
        id_start = 0
        total = 0

        while id_start <= id_max:
            id_end = id_start + range_size

            # Adicionar filtro de faixa aos kwargs
            kwargs['id_range'] = (id_column, id_start, id_end)

            query = self.get_query(**kwargs)

            try:
                result = self.client.executar_query(query, timeout=180)
            except Exception as e:
                logger.warning(f"[{entity}] Erro na faixa {id_start}-{id_end}: {e}")
                id_start = id_end
                continue

            if result and result.get("rows"):
                rows = result["rows"]
                df_range = pd.DataFrame(rows, columns=columns)
                all_dfs.append(df_range)
                total += len(rows)
                logger.debug(f"[{entity}] Faixa {id_start}-{id_end}: +{len(rows)} (total: {total})")

            id_start = id_end

        if not all_dfs:
            logger.warning(f"[{entity}] Nenhum dado extraído")
            return pd.DataFrame(columns=columns)

        df = pd.concat(all_dfs, ignore_index=True)
        logger.info(f"[{entity}] Total extraído: {len(df)} registros")

        return df

    def get_metadata(self) -> Dict[str, Any]:
        """
        Retorna metadados da extração.

        Returns:
            Dicionário com metadados (entity, timestamp, columns, etc)
        """
        return {
            "entity": self.get_entity_name(),
            "timestamp": datetime.now().isoformat(),
            "columns": self.get_columns(),
            "source": "sankhya_api"
        }
