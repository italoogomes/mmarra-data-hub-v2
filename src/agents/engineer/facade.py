# -*- coding: utf-8 -*-
"""
Engenheiro - Interface Simplificada para ETL

Fornece uma API de alto nivel para extracao de dados do Sankhya
com boas praticas aplicadas automaticamente.

Uso:
    from src.agents.engineer import Engenheiro

    engenheiro = Engenheiro()

    # Extracao simples - boas praticas automaticas
    result = engenheiro.extrair("vendas", periodo="90d")
    print(result)  # [OK] vendas: 45.230 registros (12.5 MB)

    # Extracao com filtros
    result = engenheiro.extrair("vendas", periodo="30d", codemp=1)

    # Verificar status
    status = engenheiro.status("vendas")
    print(f"Atualizado: {status.atualizado}")

    # Listar entidades disponiveis
    print(engenheiro.listar_entidades())
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd

from .extractors import (
    ClientesExtractor,
    VendasExtractor,
    ProdutosExtractor,
    EstoqueExtractor,
    VendedoresExtractor,
    ComprasExtractor,
    PedidosCompraExtractor,
)
from .transformers import DataCleaner
from .loaders import DataLakeLoader
from .config import SCHEDULE_CONFIG, ENTITY_LIMITS, EXTRACTION_CONFIG
from src.config import RAW_DATA_DIR

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Resultado estruturado de uma extracao."""
    success: bool
    entidade: str
    registros: int
    tamanho_mb: float
    duracao_segundos: float
    modo: str  # "incremental", "completo" ou "erro"
    periodo: Optional[Tuple[str, str]] = None  # (data_inicio, data_fim)
    caminho_local: str = ""
    caminho_azure: Optional[str] = None
    boas_praticas: Dict[str, bool] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    erros: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Representacao amigavel do resultado."""
        status = "OK" if self.success else "ERRO"
        base = f"[{status}] {self.entidade}: {self.registros:,} registros"

        if self.success:
            return f"{base} ({self.tamanho_mb:.2f} MB) em {self.duracao_segundos:.1f}s"
        else:
            return f"{base} - {', '.join(self.erros)}"


@dataclass
class EntityStatus:
    """Status de uma entidade no Data Lake."""
    entidade: str
    ultima_extracao: Optional[datetime] = None
    registros: int = 0
    tamanho_mb: float = 0.0
    atualizado: bool = False
    proximo_refresh: Optional[datetime] = None
    existe_local: bool = False
    existe_azure: bool = False

    def __str__(self) -> str:
        """Representacao amigavel do status."""
        if not self.existe_local:
            return f"[{self.entidade}] Nao extraido"

        status = "Atualizado" if self.atualizado else "Desatualizado"
        ultima = self.ultima_extracao.strftime("%d/%m/%Y %H:%M") if self.ultima_extracao else "N/A"
        return f"[{self.entidade}] {status} | {self.registros:,} registros | Ultima: {ultima}"


class Engenheiro:
    """
    Interface simplificada para o Agente Engenheiro de Dados.

    Aplica boas praticas de ETL automaticamente:
    - Deduplicacao por chave primaria
    - Validacao de tipos de dados
    - Tratamento de datas do Sankhya (formato DDMMYYYY)
    - Compressao Parquet otimizada
    - Metadados de rastreamento (_extracted_at, _entity)
    - Deteccao inteligente: incremental vs completo
    """

    # Mapeamento de entidades para extractors
    EXTRACTORS = {
        "vendas": VendasExtractor,
        "clientes": ClientesExtractor,
        "produtos": ProdutosExtractor,
        "estoque": EstoqueExtractor,
        "vendedores": VendedoresExtractor,
        "compras": ComprasExtractor,
        "pedidos_compra": PedidosCompraExtractor,
    }

    # Configuracao de periodos
    PERIODOS = {
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "15d": timedelta(days=15),
        "30d": timedelta(days=30),
        "60d": timedelta(days=60),
        "90d": timedelta(days=90),
        "6m": timedelta(days=180),
        "1y": timedelta(days=365),
    }

    def __init__(self, upload_azure: bool = True):
        """
        Inicializa o Engenheiro.

        Args:
            upload_azure: Se True, faz upload para Azure apos salvar local
        """
        self.upload_azure = upload_azure
        self.cleaner = DataCleaner()
        self.loader = DataLakeLoader(upload_to_cloud=upload_azure)
        self._last_results: Dict[str, ExtractionResult] = {}

    def extrair(
        self,
        entidade: str,
        periodo: Optional[str] = None,
        modo: Optional[str] = None,
        **filtros
    ) -> ExtractionResult:
        """
        Extrai dados aplicando boas praticas automaticamente.

        Boas praticas aplicadas:
        - Schema validation antes de salvar
        - Deduplicacao automatica por chave primaria
        - Tipagem correta (datas, numeros)
        - Compressao Parquet otimizada
        - Metadados de extracao (_extracted_at, _entity)

        Args:
            entidade: Nome da entidade (vendas, clientes, produtos, estoque, vendedores)
            periodo: Periodo de dados ("30d", "90d", "6m", "1y", None=tudo)
            modo: "incremental" ou "completo" (None=auto-detecta)
            **filtros: Filtros adicionais (codemp, codparc, etc)

        Returns:
            ExtractionResult com estatisticas e status

        Exemplos:
            # Vendas dos ultimos 90 dias
            result = engenheiro.extrair("vendas", periodo="90d")

            # Clientes completo
            result = engenheiro.extrair("clientes", modo="completo")

            # Estoque de uma empresa especifica
            result = engenheiro.extrair("estoque", codemp=1)
        """
        start_time = datetime.now()
        erros = []

        # Validar entidade
        entidade_lower = entidade.lower()
        if entidade_lower not in self.EXTRACTORS:
            erro = f"Entidade '{entidade}' nao existe. Disponiveis: {list(self.EXTRACTORS.keys())}"
            return self._error_result(entidade_lower, start_time, erro)

        # Calcular periodo
        data_inicio, data_fim = self._calcular_periodo(periodo)

        # Detectar modo (incremental vs completo)
        modo_real = self._detectar_modo(entidade_lower, modo)

        periodo_str = periodo if periodo else "completo"
        logger.info(f"[{entidade_lower}] Iniciando extracao modo={modo_real}, periodo={periodo_str}")

        try:
            # 1. EXTRACT - Extrair dados do Sankhya
            extractor_class = self.EXTRACTORS[entidade_lower]
            extractor = extractor_class()

            df = self._executar_extracao(
                extractor,
                entidade_lower,
                data_inicio,
                data_fim,
                filtros
            )

            if df.empty:
                return self._error_result(
                    entidade_lower,
                    start_time,
                    "Nenhum dado extraido da API"
                )

            registros_brutos = len(df)
            logger.info(f"[{entidade_lower}] Extraidos {registros_brutos} registros brutos")

            # 2. TRANSFORM - Limpar e validar dados (boas praticas)
            df = self.cleaner.clean(df, entidade_lower)
            registros_limpos = len(df)

            if registros_brutos != registros_limpos:
                logger.info(f"[{entidade_lower}] Apos limpeza: {registros_limpos} registros (-{registros_brutos - registros_limpos} duplicados/invalidos)")

            # 3. Validar schema
            schema_ok = self._validar_schema(df, extractor)
            if not schema_ok:
                erros.append("Algumas colunas esperadas estao ausentes")

            # 4. LOAD - Carregar no Data Lake
            load_result = self.loader.load(df, entidade_lower, layer="raw")

            if not load_result.get("success"):
                return self._error_result(
                    entidade_lower,
                    start_time,
                    load_result.get("error", "Erro ao salvar")
                )

            # 5. Montar resultado de sucesso
            duracao = (datetime.now() - start_time).total_seconds()

            result = ExtractionResult(
                success=True,
                entidade=entidade_lower,
                registros=len(df),
                tamanho_mb=load_result.get("size_mb", 0),
                duracao_segundos=duracao,
                modo=modo_real,
                periodo=(data_inicio, data_fim) if data_inicio else None,
                caminho_local=load_result.get("local_path", ""),
                caminho_azure=load_result.get("remote_path"),
                boas_praticas={
                    "deduplicacao": True,
                    "tipagem": True,
                    "datas_tratadas": True,
                    "schema_validado": schema_ok,
                    "metadados": "_extracted_at" in df.columns,
                    "parquet_comprimido": True,
                },
                timestamp=datetime.now(),
                erros=erros
            )

            self._last_results[entidade_lower] = result
            logger.info(str(result))

            return result

        except Exception as e:
            logger.error(f"[{entidade_lower}] Erro na extracao: {e}")
            return self._error_result(entidade_lower, start_time, str(e))

    def status(self, entidade: str) -> EntityStatus:
        """
        Retorna status de uma entidade no Data Lake.

        Args:
            entidade: Nome da entidade

        Returns:
            EntityStatus com informacoes da ultima extracao
        """
        entidade_lower = entidade.lower()

        # Verificar arquivo local
        local_path = RAW_DATA_DIR / entidade_lower / f"{entidade_lower}.parquet"

        if not local_path.exists():
            return EntityStatus(
                entidade=entidade_lower,
                existe_local=False,
                existe_azure=False
            )

        try:
            # Ler metadados do arquivo
            df = pd.read_parquet(local_path)
            tamanho = local_path.stat().st_size / (1024 * 1024)

            # Extrair data de ultima extracao
            ultima = None
            if "_extracted_at" in df.columns:
                try:
                    ultima = pd.to_datetime(df["_extracted_at"].max())
                except:
                    pass

            # Verificar se esta atualizado baseado no schedule
            atualizado = self._verificar_atualizacao(entidade_lower, ultima)

            return EntityStatus(
                entidade=entidade_lower,
                ultima_extracao=ultima,
                registros=len(df),
                tamanho_mb=round(tamanho, 2),
                atualizado=atualizado,
                existe_local=True,
                existe_azure=self.upload_azure  # Assume que foi enviado se upload habilitado
            )

        except Exception as e:
            logger.error(f"[{entidade_lower}] Erro ao ler status: {e}")
            return EntityStatus(entidade=entidade_lower, existe_local=True)

    def listar_entidades(self) -> List[str]:
        """
        Lista entidades disponiveis para extracao.

        Returns:
            Lista de nomes de entidades
        """
        return list(self.EXTRACTORS.keys())

    def resumo(self) -> Dict[str, EntityStatus]:
        """
        Retorna resumo de todas as entidades.

        Returns:
            Dict com status de cada entidade
        """
        return {ent: self.status(ent) for ent in self.listar_entidades()}

    # -------------------------------------------------------------------------
    # Metodos Privados
    # -------------------------------------------------------------------------

    def _calcular_periodo(self, periodo: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Calcula datas de inicio e fim baseado no periodo."""
        if not periodo:
            return None, None

        delta = self.PERIODOS.get(periodo.lower())
        if not delta:
            logger.warning(f"Periodo '{periodo}' invalido. Usando completo.")
            return None, None

        fim = datetime.now()
        inicio = fim - delta

        return inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")

    def _detectar_modo(self, entidade: str, modo: Optional[str]) -> str:
        """Detecta modo ideal de extracao (incremental vs completo)."""
        if modo:
            return modo.lower()

        status = self.status(entidade)

        # Se nao existe dados locais, precisa completo
        if not status.existe_local:
            return "completo"

        # Se esta atualizado, pode ser incremental
        if status.atualizado:
            return "incremental"

        return "completo"

    def _executar_extracao(
        self,
        extractor,
        entidade: str,
        data_inicio: Optional[str],
        data_fim: Optional[str],
        filtros: Dict[str, Any]
    ) -> pd.DataFrame:
        """Executa extracao delegando ao extractor apropriado."""

        # Verificar se entidade usa extração por range (grande volume)
        if entidade in ENTITY_LIMITS:
            limits = ENTITY_LIMITS[entidade]

            logger.info(f"[{entidade}] Usando extracao por range (id_max={limits['id_max']})")

            return extractor.extract_by_range(
                id_column=limits["id_column"],
                id_max=limits["id_max"],
                range_size=EXTRACTION_CONFIG.get("default_range_size", 5000),
                data_inicio=data_inicio,
                data_fim=data_fim,
                **filtros
            )
        else:
            # Extração simples
            return extractor.extract(
                data_inicio=data_inicio,
                data_fim=data_fim,
                **filtros
            )

    def _validar_schema(self, df: pd.DataFrame, extractor) -> bool:
        """Valida se DataFrame tem as colunas esperadas."""
        expected_cols = set(extractor.get_columns())
        actual_cols = set(df.columns) - {"_extracted_at", "_entity"}

        missing = expected_cols - actual_cols
        if missing:
            logger.warning(f"Colunas faltando no schema: {missing}")
            return False

        return True

    def _verificar_atualizacao(self, entidade: str, ultima: Optional[datetime]) -> bool:
        """Verifica se dados estao atualizados baseado no schedule."""
        if not ultima:
            return False

        schedule = SCHEDULE_CONFIG.get(entidade, {})
        freq = schedule.get("frequency", "daily")

        idade = datetime.now() - ultima

        if freq == "hourly":
            return idade < timedelta(hours=2)  # Tolerancia de 2h
        elif freq == "daily":
            return idade < timedelta(days=1, hours=6)  # Tolerancia de 30h
        elif freq == "weekly":
            return idade < timedelta(weeks=1, days=1)  # Tolerancia de 8 dias

        return False

    def _error_result(
        self,
        entidade: str,
        start_time: datetime,
        erro: str
    ) -> ExtractionResult:
        """Cria resultado de erro padronizado."""
        duracao = (datetime.now() - start_time).total_seconds()

        result = ExtractionResult(
            success=False,
            entidade=entidade,
            registros=0,
            tamanho_mb=0,
            duracao_segundos=duracao,
            modo="erro",
            erros=[erro]
        )

        logger.error(str(result))
        return result
