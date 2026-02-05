# -*- coding: utf-8 -*-
"""
Orchestrator - Coordena o Pipeline ETL

Responsável por:
- Orquestrar Extract → Transform → Load
- Gerenciar dependências entre entidades
- Controlar execução paralela ou sequencial
- Gerar relatórios de execução
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .extractors import (
    ClientesExtractor,
    VendasExtractor,
    ProdutosExtractor,
    EstoqueExtractor,
    VendedoresExtractor
)
from .transformers import DataCleaner, DataMapper
from .loaders import DataLakeLoader

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orquestra o pipeline ETL do Agente Engenheiro.

    Exemplo de uso:
        orchestrator = Orchestrator()

        # Executar pipeline completo
        results = orchestrator.run_full_pipeline()

        # Executar entidades específicas
        results = orchestrator.run_pipeline(entities=["clientes", "produtos"])

        # Executar apenas extração
        df = orchestrator.extract("clientes")
    """

    # Configuração de entidades
    ENTITIES = {
        "vendedores": {
            "extractor": VendedoresExtractor,
            "priority": 1,
            "use_range": False,
            "description": "Vendedores e compradores"
        },
        "clientes": {
            "extractor": ClientesExtractor,
            "priority": 2,
            "use_range": True,
            "range_config": {"id_column": "p.CODPARC", "id_max": 100000, "range_size": 5000},
            "description": "Clientes e parceiros"
        },
        "produtos": {
            "extractor": ProdutosExtractor,
            "priority": 3,
            "use_range": True,
            "range_config": {"id_column": "p.CODPROD", "id_max": 600000, "range_size": 5000},
            "description": "Catálogo de produtos"
        },
        "estoque": {
            "extractor": EstoqueExtractor,
            "priority": 4,
            "use_range": True,
            "range_config": {"id_column": "e.CODPROD", "id_max": 600000, "range_size": 5000},
            "description": "Posição de estoque"
        },
        "vendas": {
            "extractor": VendasExtractor,
            "priority": 5,
            "use_range": False,
            "description": "Notas de venda com itens"
        }
    }

    def __init__(
        self,
        upload_to_cloud: bool = True,
        clean_data: bool = True,
        map_data: bool = False
    ):
        """
        Inicializa o orchestrator.

        Args:
            upload_to_cloud: Fazer upload para Azure Data Lake
            clean_data: Aplicar limpeza de dados
            map_data: Aplicar mapeamento de colunas
        """
        self.upload_to_cloud = upload_to_cloud
        self.clean_data = clean_data
        self.map_data = map_data

        self.cleaner = DataCleaner()
        self.mapper = DataMapper()
        self.loader = DataLakeLoader(upload_to_cloud=upload_to_cloud)

        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Executa o pipeline completo para todas as entidades.

        Returns:
            Dict com resultados de cada entidade
        """
        entities = list(self.ENTITIES.keys())
        return self.run_pipeline(entities=entities)

    def run_pipeline(
        self,
        entities: List[str],
        parallel: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa o pipeline para entidades específicas.

        Args:
            entities: Lista de entidades a processar
            parallel: Executar em paralelo (experimental)
            **kwargs: Argumentos adicionais para extractors

        Returns:
            Dict com resultados de cada entidade
        """
        self.start_time = datetime.now()
        self.results = {}

        print("=" * 60)
        print("AGENTE ENGENHEIRO DE DADOS - Pipeline ETL")
        print("=" * 60)
        print(f"Início: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Entidades: {', '.join(entities)}")
        print(f"Upload Azure: {'Sim' if self.upload_to_cloud else 'Não'}")
        print("=" * 60)

        # Ordenar por prioridade
        sorted_entities = sorted(
            entities,
            key=lambda e: self.ENTITIES.get(e, {}).get("priority", 99)
        )

        if parallel:
            self._run_parallel(sorted_entities, **kwargs)
        else:
            self._run_sequential(sorted_entities, **kwargs)

        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        # Resumo
        self._print_summary(duration)

        return self.results

    def _run_sequential(self, entities: List[str], **kwargs):
        """Executa entidades sequencialmente."""
        for entity in entities:
            print(f"\n>>> {entity.upper()}")
            self.results[entity] = self._process_entity(entity, **kwargs)

    def _run_parallel(self, entities: List[str], max_workers: int = 3, **kwargs):
        """Executa entidades em paralelo."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._process_entity, entity, **kwargs): entity
                for entity in entities
            }

            for future in as_completed(futures):
                entity = futures[future]
                try:
                    self.results[entity] = future.result()
                except Exception as e:
                    self.results[entity] = {"success": False, "error": str(e)}

    def _process_entity(self, entity: str, **kwargs) -> Dict[str, Any]:
        """
        Processa uma entidade (E-T-L).

        Args:
            entity: Nome da entidade
            **kwargs: Argumentos adicionais

        Returns:
            Dict com resultado do processamento
        """
        if entity not in self.ENTITIES:
            logger.error(f"Entidade '{entity}' não configurada")
            return {"success": False, "error": "Entidade não configurada"}

        config = self.ENTITIES[entity]
        result = {
            "entity": entity,
            "success": False,
            "records": 0,
            "stages": {}
        }

        try:
            # === EXTRACT ===
            logger.info(f"[{entity}] EXTRACT...")
            extractor = config["extractor"]()

            if config.get("use_range"):
                range_cfg = config["range_config"]
                df = extractor.extract_by_range(
                    id_column=range_cfg["id_column"],
                    id_max=range_cfg["id_max"],
                    range_size=range_cfg["range_size"],
                    **kwargs
                )
            else:
                df = extractor.extract(**kwargs)

            result["stages"]["extract"] = {
                "success": not df.empty,
                "records": len(df)
            }

            if df.empty:
                logger.warning(f"[{entity}] Extração vazia")
                return result

            # === TRANSFORM ===
            if self.clean_data:
                logger.info(f"[{entity}] TRANSFORM (clean)...")
                df = self.cleaner.clean(df, entity)
                result["stages"]["clean"] = {
                    "success": True,
                    "records": len(df)
                }

            if self.map_data:
                logger.info(f"[{entity}] TRANSFORM (map)...")
                df = self.mapper.map(df, entity)
                result["stages"]["map"] = {
                    "success": True,
                    "records": len(df)
                }

            # === LOAD ===
            logger.info(f"[{entity}] LOAD...")
            load_result = self.loader.load(df, entity, layer="raw")

            result["stages"]["load"] = load_result
            result["success"] = load_result.get("success", False)
            result["records"] = load_result.get("records", 0)
            result["size_mb"] = load_result.get("size_mb", 0)

            return result

        except Exception as e:
            logger.error(f"[{entity}] Erro: {e}")
            result["error"] = str(e)
            return result

    def extract(self, entity: str, **kwargs):
        """
        Executa apenas a extração de uma entidade.

        Args:
            entity: Nome da entidade
            **kwargs: Argumentos para o extractor

        Returns:
            DataFrame com dados extraídos
        """
        if entity not in self.ENTITIES:
            raise ValueError(f"Entidade '{entity}' não configurada")

        config = self.ENTITIES[entity]
        extractor = config["extractor"]()

        if config.get("use_range"):
            range_cfg = config["range_config"]
            return extractor.extract_by_range(
                id_column=range_cfg["id_column"],
                id_max=range_cfg["id_max"],
                range_size=range_cfg["range_size"],
                **kwargs
            )
        else:
            return extractor.extract(**kwargs)

    def _print_summary(self, duration: float):
        """Imprime resumo da execução."""
        print("\n" + "=" * 60)
        print("RESUMO")
        print("=" * 60)

        total_records = 0
        total_size = 0
        successes = 0

        for entity, result in self.results.items():
            status = "[OK]" if result.get("success") else "[X]"
            records = result.get("records", 0)
            size = result.get("size_mb", 0)

            print(f"  {status} {entity:<12}: {records:>10,} registros | {size:>6.2f} MB".replace(",", "."))

            total_records += records
            total_size += size
            if result.get("success"):
                successes += 1

        print("-" * 60)
        print(f"  TOTAL: {total_records:>10,} registros | {total_size:>6.2f} MB".replace(",", "."))
        print(f"  Duração: {duration:.1f} segundos")
        print(f"  Status: {successes}/{len(self.results)} bem-sucedidas")
        print("=" * 60)

    def get_results(self) -> Dict[str, Any]:
        """Retorna resultados da última execução."""
        return {
            "results": self.results,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": (self.end_time - self.start_time).total_seconds() if self.end_time else None
        }


# Entry point para execução via linha de comando
def main():
    """Executa o pipeline via CLI."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="Agente Engenheiro de Dados")
    parser.add_argument(
        "--entities",
        nargs="+",
        help="Entidades a processar (default: todas)"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Não fazer upload para Azure"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Não aplicar limpeza de dados"
    )
    parser.add_argument(
        "--map",
        action="store_true",
        help="Aplicar mapeamento de colunas"
    )

    args = parser.parse_args()

    orchestrator = Orchestrator(
        upload_to_cloud=not args.no_upload,
        clean_data=not args.no_clean,
        map_data=args.map
    )

    if args.entities:
        results = orchestrator.run_pipeline(entities=args.entities)
    else:
        results = orchestrator.run_full_pipeline()

    # Retornar código de erro se alguma falhou
    return 0 if all(r.get("success") for r in results.values()) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
