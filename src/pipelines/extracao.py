# -*- coding: utf-8 -*-
"""
Pipeline de Extração - Sankhya → Azure Data Lake

Este pipeline orquestra a extração de dados do ERP Sankhya
e carrega no Azure Data Lake em formato Parquet.
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
import pandas as pd

from src.utils.sankhya_client import SankhyaClient
from src.utils.azure_storage import AzureDataLakeClient
from src.config import RAW_DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineExtracao:
    """
    Pipeline de extração de dados do Sankhya para o Data Lake.

    Fluxo:
    1. Autenticar no Sankhya
    2. Conectar ao Azure Data Lake
    3. Para cada entidade configurada:
       a. Extrair dados via API
       b. Salvar localmente em Parquet
       c. Upload para Data Lake
    4. Gerar relatório de execução
    """

    # Configuração das entidades para extração
    ENTIDADES = {
        "vendedores": {
            "query": """
                SELECT v.CODVEND, v.APELIDO, v.ATIVO, v.TIPVEND, v.EMAIL, v.CODGER
                FROM TGFVEN v ORDER BY v.CODVEND
            """,
            "colunas": ["CODVEND", "APELIDO", "ATIVO", "TIPVEND", "EMAIL", "CODGER"],
            "caminho_datalake": "raw/vendedores/vendedores.parquet",
            "usa_faixa": False
        },
        "clientes": {
            "query_template": """
                SELECT p.CODPARC, p.NOMEPARC, p.RAZAOSOCIAL, p.CGC_CPF, p.TIPPESSOA,
                       p.CLIENTE, p.FORNECEDOR, p.ATIVO, p.EMAIL, p.TELEFONE, p.CEP,
                       p.CODCID, p.CODVEND, p.LIMCRED
                FROM TGFPAR p
                WHERE p.ATIVO = 'S' AND {WHERE_FAIXA}
                ORDER BY p.CODPARC
            """,
            "colunas": ["CODPARC", "NOMEPARC", "RAZAOSOCIAL", "CGC_CPF", "TIPPESSOA",
                        "CLIENTE", "FORNECEDOR", "ATIVO", "EMAIL", "TELEFONE", "CEP",
                        "CODCID", "CODVEND", "LIMCRED"],
            "caminho_datalake": "raw/clientes/clientes.parquet",
            "usa_faixa": True,
            "campo_id": "p.CODPARC",
            "id_max": 100000,
            "faixa_size": 5000
        },
        "produtos": {
            "query_template": """
                SELECT p.CODPROD, p.DESCRPROD, p.REFERENCIA, p.MARCA, p.CODGRUPOPROD,
                       p.ATIVO, p.USOPROD, p.NCM, p.CODVOL, p.PESOBRUTO, p.PESOLIQ
                FROM TGFPRO p
                WHERE p.ATIVO = 'S' AND {WHERE_FAIXA}
                ORDER BY p.CODPROD
            """,
            "colunas": ["CODPROD", "DESCRPROD", "REFERENCIA", "MARCA", "CODGRUPOPROD",
                        "ATIVO", "USOPROD", "NCM", "CODVOL", "PESOBRUTO", "PESOLIQ"],
            "caminho_datalake": "raw/produtos/produtos.parquet",
            "usa_faixa": True,
            "campo_id": "p.CODPROD",
            "id_max": 600000,
            "faixa_size": 5000
        },
        "estoque": {
            "query_template": """
                SELECT e.CODEMP, e.CODPROD, p.DESCRPROD, e.CODLOCAL, e.CONTROLE,
                       NVL(e.ESTOQUE, 0) AS ESTOQUE, NVL(e.RESERVADO, 0) AS RESERVADO,
                       NVL(e.ESTOQUE, 0) - NVL(e.RESERVADO, 0) AS DISPONIVEL
                FROM TGFEST e
                LEFT JOIN TGFPRO p ON p.CODPROD = e.CODPROD
                WHERE e.CODEMP = 1 AND NVL(e.ESTOQUE, 0) > 0 AND {WHERE_FAIXA}
                ORDER BY e.CODPROD
            """,
            "colunas": ["CODEMP", "CODPROD", "DESCRPROD", "CODLOCAL", "CONTROLE",
                        "ESTOQUE", "RESERVADO", "DISPONIVEL"],
            "caminho_datalake": "raw/estoque/estoque.parquet",
            "usa_faixa": True,
            "campo_id": "e.CODPROD",
            "id_max": 600000,
            "faixa_size": 5000
        }
    }

    def __init__(self):
        """Inicializa o pipeline"""
        self.sankhya = None
        self.azure = None
        self.resultados = []

    def _autenticar_sankhya(self) -> bool:
        """Autentica no Sankhya"""
        logger.info("Autenticando no Sankhya...")
        self.sankhya = SankhyaClient()
        if not self.sankhya.autenticar():
            logger.error("Falha na autenticação Sankhya")
            return False
        logger.info("Autenticado com sucesso")
        return True

    def _conectar_azure(self) -> bool:
        """Conecta ao Azure Data Lake"""
        logger.info("Conectando ao Azure Data Lake...")
        self.azure = AzureDataLakeClient()
        if not self.azure.testar_conexao():
            logger.error("Falha na conexão Azure")
            return False
        logger.info("Conectado ao Azure Data Lake")
        return True

    def _extrair_simples(self, query: str, colunas: list) -> pd.DataFrame:
        """Extrai dados com query simples (sem paginação)"""
        result = self.sankhya.executar_query(query)
        if result and result.get("rows"):
            return pd.DataFrame(result["rows"], columns=colunas)
        return pd.DataFrame(columns=colunas)

    def _extrair_por_faixas(
        self,
        query_template: str,
        campo_id: str,
        colunas: list,
        id_max: int,
        faixa_size: int
    ) -> pd.DataFrame:
        """Extrai dados em faixas para contornar limite da API"""
        all_dfs = []
        id_inicio = 0
        total = 0

        while id_inicio <= id_max:
            id_fim = id_inicio + faixa_size
            where_faixa = f"{campo_id} >= {id_inicio} AND {campo_id} < {id_fim}"
            query = query_template.replace("{WHERE_FAIXA}", where_faixa)

            result = self.sankhya.executar_query(query, timeout=180)

            if result and result.get("rows"):
                rows = result["rows"]
                df_faixa = pd.DataFrame(rows, columns=colunas)
                all_dfs.append(df_faixa)
                total += len(rows)
                logger.debug(f"  Faixa {id_inicio}-{id_fim}: +{len(rows)} (total: {total})")

            id_inicio = id_fim

        if not all_dfs:
            return pd.DataFrame(columns=colunas)

        return pd.concat(all_dfs, ignore_index=True)

    def _salvar_e_upload(
        self,
        df: pd.DataFrame,
        nome: str,
        caminho_datalake: str
    ) -> Dict:
        """Salva localmente e faz upload para o Data Lake"""
        resultado = {
            "entidade": nome,
            "registros": len(df),
            "sucesso": False,
            "tamanho_mb": 0
        }

        if df.empty:
            logger.warning(f"  {nome}: Nenhum dado extraído")
            return resultado

        # Salvar localmente
        arquivo = RAW_DATA_DIR / nome / f"{nome}.parquet"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(arquivo, index=False)

        tamanho_mb = arquivo.stat().st_size / (1024 * 1024)
        resultado["tamanho_mb"] = tamanho_mb

        logger.info(f"  {nome}: {len(df)} registros ({tamanho_mb:.2f} MB)")

        # Upload para Azure
        if self.azure.upload_arquivo(arquivo, caminho_datalake):
            resultado["sucesso"] = True
            logger.info(f"  {nome}: Upload concluído")
        else:
            logger.error(f"  {nome}: Falha no upload")

        return resultado

    def executar(
        self,
        entidades: Optional[List[str]] = None,
        verbose: bool = True
    ) -> List[Dict]:
        """
        Executa o pipeline de extração.

        Args:
            entidades: Lista de entidades para extrair (None = todas)
            verbose: Se True, mostra progresso detalhado

        Returns:
            Lista de resultados por entidade
        """
        inicio = datetime.now()

        print("=" * 60)
        print("PIPELINE DE EXTRAÇÃO - MMarra Data Hub")
        print("=" * 60)
        print(f"Início: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Autenticar
        if not self._autenticar_sankhya():
            return []

        if not self._conectar_azure():
            return []

        # Determinar entidades
        if entidades is None:
            entidades = list(self.ENTIDADES.keys())

        self.resultados = []

        # Processar cada entidade
        for nome in entidades:
            if nome not in self.ENTIDADES:
                logger.warning(f"Entidade '{nome}' não configurada")
                continue

            config = self.ENTIDADES[nome]
            print(f"\n>>> {nome.upper()}")

            # Extrair
            if config.get("usa_faixa"):
                df = self._extrair_por_faixas(
                    config["query_template"],
                    config["campo_id"],
                    config["colunas"],
                    config["id_max"],
                    config["faixa_size"]
                )
            else:
                df = self._extrair_simples(config["query"], config["colunas"])

            # Salvar e upload
            resultado = self._salvar_e_upload(df, nome, config["caminho_datalake"])
            self.resultados.append(resultado)

        # Resumo final
        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()

        print("\n" + "=" * 60)
        print("RESUMO")
        print("=" * 60)

        total_registros = 0
        total_mb = 0
        sucessos = 0

        for r in self.resultados:
            status = "✓" if r["sucesso"] else "✗"
            print(f"  {status} {r['entidade']:<12}: {r['registros']:>10,} registros | {r['tamanho_mb']:>6.2f} MB".replace(",", "."))
            total_registros += r["registros"]
            total_mb += r["tamanho_mb"]
            if r["sucesso"]:
                sucessos += 1

        print("-" * 60)
        print(f"  TOTAL: {total_registros:>10,} registros | {total_mb:>6.2f} MB".replace(",", "."))
        print(f"  Duração: {duracao:.1f} segundos")
        print(f"  Status: {sucessos}/{len(self.resultados)} extrações bem-sucedidas")
        print("=" * 60)

        return self.resultados


def main():
    """Executa o pipeline completo"""
    pipeline = PipelineExtracao()
    resultados = pipeline.executar()
    return 0 if all(r["sucesso"] for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
