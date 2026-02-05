# -*- coding: utf-8 -*-
"""
Cliente para Azure Data Lake Storage Gen2
"""

import logging
from pathlib import Path
from typing import Optional, List

from azure.storage.filedatalake import DataLakeServiceClient

from src.config import (
    AZURE_STORAGE_ACCOUNT,
    AZURE_STORAGE_KEY,
    AZURE_CONTAINER
)

logger = logging.getLogger(__name__)


class AzureDataLakeClient:
    """Cliente para upload/download no Azure Data Lake"""

    def __init__(
        self,
        account_name: str = None,
        account_key: str = None,
        container_name: str = None
    ):
        self.account_name = account_name or AZURE_STORAGE_ACCOUNT
        self.account_key = account_key or AZURE_STORAGE_KEY
        self.container_name = container_name or AZURE_CONTAINER

        self._service_client = None
        self._file_system_client = None

    def _get_service_client(self) -> DataLakeServiceClient:
        """Retorna o cliente do serviço Data Lake"""
        if self._service_client is None:
            account_url = f"https://{self.account_name}.dfs.core.windows.net"
            self._service_client = DataLakeServiceClient(
                account_url=account_url,
                credential=self.account_key
            )
        return self._service_client

    def _get_file_system_client(self):
        """Retorna o cliente do container (file system)"""
        if self._file_system_client is None:
            service = self._get_service_client()
            self._file_system_client = service.get_file_system_client(
                file_system=self.container_name
            )
        return self._file_system_client

    def testar_conexao(self) -> bool:
        """Testa a conexão com o Data Lake"""
        try:
            fs_client = self._get_file_system_client()
            # Tenta listar para verificar se tem acesso
            paths = list(fs_client.get_paths(path="/", max_results=1))
            logger.info(f"Conexão OK com container '{self.container_name}'")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            return False

    def listar_pastas(self, caminho: str = "/") -> List[str]:
        """Lista pastas/arquivos em um caminho"""
        try:
            fs_client = self._get_file_system_client()
            paths = fs_client.get_paths(path=caminho)
            return [p.name for p in paths]
        except Exception as e:
            logger.error(f"Erro ao listar: {e}")
            return []

    def criar_pasta(self, caminho: str) -> bool:
        """Cria uma pasta (diretório) no Data Lake"""
        try:
            fs_client = self._get_file_system_client()
            directory_client = fs_client.create_directory(caminho)
            logger.info(f"Pasta criada: {caminho}")
            return True
        except Exception as e:
            if "PathAlreadyExists" in str(e):
                logger.info(f"Pasta ja existe: {caminho}")
                return True
            logger.error(f"Erro ao criar pasta: {e}")
            return False

    def upload_arquivo(
        self,
        arquivo_local,
        caminho_destino: str,
        sobrescrever: bool = True
    ) -> bool:
        """
        Faz upload de um arquivo para o Data Lake.

        Args:
            arquivo_local: Path ou string do arquivo local
            caminho_destino: Caminho no Data Lake (ex: 'raw/vendas/arquivo.parquet')
            sobrescrever: Se deve sobrescrever se existir

        Returns:
            True se sucesso
        """
        try:
            # Garantir que arquivo_local seja Path
            arquivo_local = Path(arquivo_local)

            fs_client = self._get_file_system_client()

            # Separar diretório e nome do arquivo
            destino = Path(caminho_destino)
            diretorio = str(destino.parent)
            nome_arquivo = destino.name

            # Criar diretório se não existir
            if diretorio and diretorio != ".":
                try:
                    fs_client.create_directory(diretorio)
                except:
                    pass  # Já existe

            # Obter cliente do arquivo
            file_client = fs_client.get_file_client(caminho_destino)

            # Fazer upload
            with open(arquivo_local, "rb") as f:
                file_client.upload_data(f, overwrite=sobrescrever)

            logger.info(f"Upload OK: {arquivo_local.name} -> {caminho_destino}")
            return True

        except Exception as e:
            logger.error(f"Erro no upload: {e}")
            return False

    def download_arquivo(
        self,
        caminho_origem: str,
        arquivo_local: Path
    ) -> bool:
        """
        Faz download de um arquivo do Data Lake.

        Args:
            caminho_origem: Caminho no Data Lake
            arquivo_local: Path local para salvar

        Returns:
            True se sucesso
        """
        try:
            fs_client = self._get_file_system_client()
            file_client = fs_client.get_file_client(caminho_origem)

            # Criar diretório local se não existir
            arquivo_local.parent.mkdir(parents=True, exist_ok=True)

            # Download
            with open(arquivo_local, "wb") as f:
                download = file_client.download_file()
                f.write(download.readall())

            logger.info(f"Download OK: {caminho_origem} -> {arquivo_local}")
            return True

        except Exception as e:
            logger.error(f"Erro no download: {e}")
            return False

    def deletar_arquivo(self, caminho: str) -> bool:
        """Deleta um arquivo do Data Lake"""
        try:
            fs_client = self._get_file_system_client()
            file_client = fs_client.get_file_client(caminho)
            file_client.delete_file()
            logger.info(f"Arquivo deletado: {caminho}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar: {e}")
            return False


def criar_estrutura_datalake():
    """
    Cria a estrutura de pastas padrão no Data Lake.

    Estrutura:
        datahub/
        ├── raw/           # Dados brutos extraídos
        │   ├── vendas/
        │   ├── clientes/
        │   ├── produtos/
        │   └── estoque/
        ├── processed/     # Dados processados/limpos
        │   ├── vendas/
        │   ├── clientes/
        │   ├── produtos/
        │   └── estoque/
        └── curated/       # Dados prontos para análise
            └── analytics/
    """
    client = AzureDataLakeClient()

    if not client.testar_conexao():
        print("[ERRO] Falha na conexão com Azure Data Lake")
        return False

    print("\nCriando estrutura de pastas no Data Lake...")

    pastas = [
        # Raw (dados brutos)
        "raw/vendas",
        "raw/clientes",
        "raw/produtos",
        "raw/estoque",
        "raw/compras",
        "raw/financeiro",
        # Processed (dados limpos)
        "processed/vendas",
        "processed/clientes",
        "processed/produtos",
        "processed/estoque",
        # Curated (dados analíticos)
        "curated/analytics",
        "curated/reports"
    ]

    sucesso = 0
    for pasta in pastas:
        if client.criar_pasta(pasta):
            print(f"  [OK] {pasta}")
            sucesso += 1
        else:
            print(f"  [X]  {pasta}")

    print(f"\n{sucesso}/{len(pastas)} pastas criadas/verificadas")
    return sucesso == len(pastas)


# Para teste direto
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("TESTE DE CONEXAO - AZURE DATA LAKE")
    print("=" * 60)

    client = AzureDataLakeClient()

    print(f"\nStorage Account: {client.account_name}")
    print(f"Container: {client.container_name}")

    if client.testar_conexao():
        print("\n[OK] Conexao estabelecida com sucesso!")

        # Listar conteúdo atual
        print("\nConteudo atual do container:")
        itens = client.listar_pastas("/")
        if itens:
            for item in itens[:20]:
                print(f"  - {item}")
        else:
            print("  (vazio)")

        # Perguntar se quer criar estrutura
        print("\n" + "=" * 60)
        resposta = input("Criar estrutura de pastas padrao? (s/n): ")
        if resposta.lower() == 's':
            criar_estrutura_datalake()

    else:
        print("\n[ERRO] Falha na conexao!")
        sys.exit(1)
