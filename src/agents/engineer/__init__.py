# -*- coding: utf-8 -*-
"""
Agente Engenheiro de Dados

Responsável pelo pipeline ETL:
- Extract: Extrai dados do Sankhya ERP via API
- Transform: Limpa, valida e transforma os dados
- Load: Carrega no Azure Data Lake em formato Parquet

Uso simplificado (RECOMENDADO):
    from src.agents.engineer import Engenheiro

    engenheiro = Engenheiro()

    # Extracao com boas praticas automaticas
    result = engenheiro.extrair("vendas", periodo="90d")
    print(result)  # [OK] vendas: 45.230 registros (12.5 MB)

    # Extracao com filtros
    result = engenheiro.extrair("clientes", modo="completo")

    # Verificar status
    status = engenheiro.status("vendas")
    print(status)  # [vendas] Atualizado | 45.230 registros | Ultima: 04/02/2026 10:30

    # Listar entidades disponiveis
    print(engenheiro.listar_entidades())  # ['vendas', 'clientes', 'produtos', ...]

Uso avancado (componentes individuais):
    from src.agents.engineer import Orchestrator, Scheduler
    from src.agents.engineer.extractors import ClientesExtractor
    from src.agents.engineer.transformers import DataCleaner, DataMapper
    from src.agents.engineer.loaders import DataLakeLoader

    # Extracao manual
    extractor = ClientesExtractor()
    df = extractor.extract(apenas_ativos=True)

    # Limpeza
    cleaner = DataCleaner()
    df = cleaner.clean(df, entity="clientes")

    # Carga
    loader = DataLakeLoader()
    loader.load(df, entity="clientes", layer="raw")

Linha de comando:
    # Pipeline completo
    python -m src.agents.engineer.orchestrator

    # Entidades especificas
    python -m src.agents.engineer.orchestrator --entities clientes produtos

    # Scheduler
    python -m src.agents.engineer.scheduler --run-once
"""

from .orchestrator import Orchestrator
from .scheduler import Scheduler
from .facade import Engenheiro, ExtractionResult, EntityStatus

__all__ = [
    # Interface simplificada (recomendada)
    'Engenheiro',
    'ExtractionResult',
    'EntityStatus',
    # Componentes avancados
    'Orchestrator',
    'Scheduler',
]
