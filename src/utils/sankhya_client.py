# -*- coding: utf-8 -*-
"""
Cliente reutilizavel para API Sankhya
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from src.config import (
    SANKHYA_CLIENT_ID,
    SANKHYA_CLIENT_SECRET,
    SANKHYA_X_TOKEN,
    SANKHYA_AUTH_URL,
    SANKHYA_QUERY_URL,
    DEFAULT_TIMEOUT
)

logger = logging.getLogger(__name__)


class SankhyaClient:
    """Cliente para interagir com a API Sankhya"""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def autenticar(self) -> bool:
        """
        Autentica na API Sankhya e obtem access_token.
        Retorna True se sucesso, False se falha.
        """
        try:
            response = requests.post(
                SANKHYA_AUTH_URL,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Token": SANKHYA_X_TOKEN
                },
                data={
                    "client_id": SANKHYA_CLIENT_ID,
                    "client_secret": SANKHYA_CLIENT_SECRET,
                    "grant_type": "client_credentials"
                },
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"Erro na autenticacao: HTTP {response.status_code}")
                return False

            data = response.json()
            self._access_token = data.get("access_token")

            # Token valido por 24h, renovar antes
            expires_in = data.get("expires_in", 86400)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)

            logger.info("Autenticacao realizada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao autenticar: {e}")
            return False

    def _garantir_token(self) -> bool:
        """Garante que o token esta valido, renovando se necessario"""
        if self._access_token is None:
            return self.autenticar()

        if self._token_expiry and datetime.now() >= self._token_expiry:
            logger.info("Token expirado, renovando...")
            return self.autenticar()

        return True

    def executar_query(
        self,
        sql: str,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Optional[Dict[str, Any]]:
        """
        Executa uma query SQL via API Sankhya.

        Args:
            sql: Query SQL a executar
            timeout: Timeout em segundos

        Returns:
            Dict com 'rows' e 'fieldsMetadata', ou None em caso de erro
        """
        if not self._garantir_token():
            logger.error("Falha ao obter token de autenticacao")
            return None

        try:
            response = requests.post(
                SANKHYA_QUERY_URL,
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json"
                },
                json={"requestBody": {"sql": sql}},
                timeout=timeout
            )

            if response.status_code == 401:
                # Token expirou, tentar renovar
                logger.warning("Token expirado (401), renovando...")
                self._access_token = None
                if not self.autenticar():
                    return None
                return self.executar_query(sql, timeout)

            if response.status_code != 200:
                logger.error(f"Erro HTTP: {response.status_code}")
                return None

            result = response.json()

            if result.get("status") != "1":
                logger.error(f"Erro na query: {result.get('statusMessage')}")
                return None

            return result.get("responseBody", {})

        except requests.Timeout:
            logger.error(f"Timeout na query (>{timeout}s)")
            return None
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            return None

    def executar_query_paginada(
        self,
        sql_base: str,
        limite_por_pagina: int = 10000,
        max_registros: Optional[int] = None
    ) -> List[List[Any]]:
        """
        Executa query com paginacao para grandes volumes.

        Args:
            sql_base: Query SQL base (sem OFFSET/FETCH)
            limite_por_pagina: Registros por pagina
            max_registros: Limite maximo total (None = sem limite)

        Returns:
            Lista com todas as rows concatenadas
        """
        all_rows = []
        offset = 0
        fields_metadata = None

        while True:
            sql_paginada = f"""
            {sql_base}
            OFFSET {offset} ROWS
            FETCH NEXT {limite_por_pagina} ROWS ONLY
            """

            result = self.executar_query(sql_paginada)

            if not result:
                break

            rows = result.get("rows", [])

            if not rows:
                break

            if fields_metadata is None:
                fields_metadata = result.get("fieldsMetadata", [])

            all_rows.extend(rows)

            logger.info(f"Extraidos {len(all_rows)} registros...")

            # Verificar limite maximo
            if max_registros and len(all_rows) >= max_registros:
                all_rows = all_rows[:max_registros]
                break

            # Se retornou menos que o limite, acabou
            if len(rows) < limite_por_pagina:
                break

            offset += limite_por_pagina

        return all_rows

    def contar_registros(self, tabela: str, where: str = "") -> int:
        """
        Conta registros em uma tabela.

        Args:
            tabela: Nome da tabela
            where: Clausula WHERE opcional (sem a palavra WHERE)

        Returns:
            Quantidade de registros
        """
        sql = f"SELECT COUNT(*) FROM {tabela}"
        if where:
            sql += f" WHERE {where}"

        result = self.executar_query(sql)

        if result and result.get("rows"):
            return int(result["rows"][0][0])

        return 0
