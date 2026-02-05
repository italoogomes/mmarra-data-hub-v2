# -*- coding: utf-8 -*-
"""
Data Lake Loader - Carrega dados no Azure Data Lake

Responsável por:
- Salvar DataFrames em formato Parquet
- Upload para Azure Data Lake Gen2
- Organizar em camadas (raw, processed, curated)
- Gerenciar versionamento e particionamento
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.utils import _AZURE_AVAILABLE

# Importar Azure apenas se disponivel
if _AZURE_AVAILABLE:
    from src.utils.azure_storage import AzureDataLakeClient
else:
    AzureDataLakeClient = None

logger = logging.getLogger(__name__)


class DataLakeLoader:
    """
    Carrega dados no Azure Data Lake.

    Exemplo de uso:
        loader = DataLakeLoader()
        loader.load(df, entity="clientes", layer="raw")
    """

    # Configuração de camadas
    LAYERS = {
        "raw": {
            "local_dir": RAW_DATA_DIR,
            "remote_path": "raw",
            "description": "Dados brutos extraídos"
        },
        "processed": {
            "local_dir": PROCESSED_DATA_DIR,
            "remote_path": "processed",
            "description": "Dados limpos e transformados"
        },
        "curated": {
            "local_dir": PROCESSED_DATA_DIR / "curated",
            "remote_path": "curated",
            "description": "Dados agregados para análise"
        }
    }

    def __init__(self, upload_to_cloud: bool = True):
        """
        Inicializa o loader.

        Args:
            upload_to_cloud: Se True, faz upload para Azure após salvar local
        """
        # Desabilitar upload se Azure nao estiver disponivel
        if upload_to_cloud and not _AZURE_AVAILABLE:
            logger.warning("Azure SDK nao instalado. Upload desabilitado.")
            upload_to_cloud = False

        self.upload_to_cloud = upload_to_cloud
        self._azure_client = None
        self.stats = {}

    @property
    def azure_client(self):
        """Retorna cliente Azure, criando se necessário."""
        if not _AZURE_AVAILABLE:
            return None

        if self._azure_client is None:
            self._azure_client = AzureDataLakeClient()
        return self._azure_client

    def load(
        self,
        df: pd.DataFrame,
        entity: str,
        layer: str = "raw",
        partition_by: Optional[str] = None,
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """
        Carrega DataFrame no Data Lake.

        Args:
            df: DataFrame a carregar
            entity: Nome da entidade (clientes, vendas, etc)
            layer: Camada de destino (raw, processed, curated)
            partition_by: Coluna para particionar (ex: data)
            overwrite: Sobrescrever arquivo existente

        Returns:
            Dict com informações da carga (path, records, size, etc)
        """
        if df.empty:
            logger.warning(f"[{entity}] DataFrame vazio, nada a carregar")
            return {"success": False, "error": "DataFrame vazio"}

        if layer not in self.LAYERS:
            logger.error(f"Camada '{layer}' inválida. Use: {list(self.LAYERS.keys())}")
            return {"success": False, "error": f"Camada inválida: {layer}"}

        layer_config = self.LAYERS[layer]
        logger.info(f"[{entity}] Carregando {len(df)} registros na camada '{layer}'...")

        # 1. Salvar localmente
        local_path = self._save_local(df, entity, layer_config["local_dir"])

        if not local_path:
            return {"success": False, "error": "Falha ao salvar localmente"}

        # Calcular tamanho
        size_mb = local_path.stat().st_size / (1024 * 1024)

        result = {
            "success": True,
            "entity": entity,
            "layer": layer,
            "records": len(df),
            "columns": len(df.columns),
            "local_path": str(local_path),
            "size_mb": round(size_mb, 2),
            "timestamp": datetime.now().isoformat()
        }

        # 2. Upload para Azure (se habilitado)
        if self.upload_to_cloud:
            remote_path = f"{layer_config['remote_path']}/{entity}/{entity}.parquet"
            upload_success = self._upload_to_azure(local_path, remote_path, overwrite)

            result["uploaded"] = upload_success
            result["remote_path"] = remote_path if upload_success else None

            if not upload_success:
                logger.warning(f"[{entity}] Upload falhou, arquivo disponível localmente")

        # Atualizar estatísticas
        self.stats[entity] = result

        logger.info(f"[{entity}] Carga concluída: {len(df)} registros ({size_mb:.2f} MB)")

        return result

    def _save_local(
        self,
        df: pd.DataFrame,
        entity: str,
        local_dir: Path
    ) -> Optional[Path]:
        """Salva DataFrame localmente em Parquet."""
        try:
            # Criar diretório se não existir
            entity_dir = local_dir / entity
            entity_dir.mkdir(parents=True, exist_ok=True)

            # Nome do arquivo
            file_path = entity_dir / f"{entity}.parquet"

            # Salvar
            df.to_parquet(file_path, index=False, engine="pyarrow")

            logger.debug(f"[{entity}] Salvo localmente: {file_path}")

            return file_path

        except Exception as e:
            logger.error(f"[{entity}] Erro ao salvar localmente: {e}")
            return None

    def _upload_to_azure(
        self,
        local_path: Path,
        remote_path: str,
        overwrite: bool
    ) -> bool:
        """Faz upload para Azure Data Lake."""
        try:
            return self.azure_client.upload_arquivo(
                str(local_path),
                remote_path,
                sobrescrever=overwrite
            )
        except Exception as e:
            logger.error(f"Erro no upload para Azure: {e}")
            return False

    def load_partitioned(
        self,
        df: pd.DataFrame,
        entity: str,
        partition_column: str,
        layer: str = "raw"
    ) -> Dict[str, Any]:
        """
        Carrega DataFrame particionado por uma coluna (ex: data).

        Args:
            df: DataFrame a carregar
            entity: Nome da entidade
            partition_column: Coluna para particionar
            layer: Camada de destino

        Returns:
            Dict com informações da carga
        """
        if partition_column not in df.columns:
            logger.error(f"Coluna '{partition_column}' não encontrada")
            return {"success": False, "error": f"Coluna não encontrada: {partition_column}"}

        results = []

        # Agrupar por partição
        for partition_value, partition_df in df.groupby(partition_column):
            # Criar nome da partição
            partition_name = f"{entity}_{partition_value}"

            result = self.load(
                partition_df,
                entity=partition_name,
                layer=layer,
                overwrite=True
            )
            results.append(result)

        total_records = sum(r.get("records", 0) for r in results)
        total_size = sum(r.get("size_mb", 0) for r in results)

        return {
            "success": all(r.get("success") for r in results),
            "entity": entity,
            "partitions": len(results),
            "total_records": total_records,
            "total_size_mb": round(total_size, 2),
            "partition_column": partition_column
        }

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de carga."""
        return self.stats

    def list_loaded_entities(self, layer: str = "raw") -> list:
        """Lista entidades carregadas em uma camada."""
        if layer not in self.LAYERS:
            return []

        local_dir = self.LAYERS[layer]["local_dir"]

        if not local_dir.exists():
            return []

        return [d.name for d in local_dir.iterdir() if d.is_dir()]
