# -*- coding: utf-8 -*-
"""
Analista - Interface Simplificada para Relatorios e KPIs

Fornece uma API de alto nivel para geracao de relatorios
com templates inteligentes baseados em receitas.

Uso:
    from src.agents.analyst import Analista

    analista = Analista()

    # Relatorio completo de vendas
    result = analista.relatorio("vendas")
    result.abrir()  # Abre no navegador

    # Relatorio com filtros
    result = analista.relatorio("vendas", cliente="CLIENTE X", periodo="30d")

    # Relatorios pre-definidos
    result = analista.relatorio("vendas_diario")
    result = analista.relatorio("estoque_critico")

    # Apenas KPIs (sem HTML)
    kpis = analista.kpis("vendas", periodo="30d")
    print(f"Faturamento: {kpis['faturamento_total']['formatted']}")
"""

import logging
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd

from .data_loader import AnalystDataLoader
from .kpis import VendasKPI, ComprasKPI, EstoqueKPI
from .reports import ReportGenerator
from .config import ANALYST_CONFIG

logger = logging.getLogger(__name__)


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class ReportResult:
    """Resultado de um relatorio gerado."""
    success: bool
    tipo: str
    titulo: str
    html: str = ""
    caminho_arquivo: Optional[str] = None
    kpis: Dict[str, Any] = field(default_factory=dict)
    filtros_aplicados: Dict[str, Any] = field(default_factory=dict)
    periodo: Tuple[str, str] = ("", "")
    registros_analisados: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    erros: List[str] = field(default_factory=list)

    def abrir(self) -> bool:
        """
        Abre o relatorio no navegador.

        Returns:
            True se abriu com sucesso, False caso contrario
        """
        if not self.caminho_arquivo:
            logger.warning("Nenhum arquivo de relatorio para abrir")
            return False

        path = Path(self.caminho_arquivo)
        if not path.exists():
            logger.warning(f"Arquivo nao encontrado: {self.caminho_arquivo}")
            return False

        try:
            webbrowser.open(f"file:///{path.resolve()}")
            return True
        except Exception as e:
            logger.error(f"Erro ao abrir navegador: {e}")
            return False

    def __str__(self) -> str:
        """Representacao amigavel do resultado."""
        if self.success:
            return f"[OK] {self.tipo}: {self.registros_analisados:,} registros analisados"
        else:
            return f"[ERRO] {self.tipo}: {', '.join(self.erros)}"


@dataclass
class ReportRecipe:
    """Define uma receita de relatorio."""
    nome: str
    descricao: str
    modulo: str  # "vendas", "compras", "estoque"
    kpis_inclusos: List[str]
    template: str
    filtros_suportados: List[str]
    periodo_padrao: Optional[str]  # None = sem filtro de periodo


# =============================================================================
# RECEITAS DE RELATORIOS
# =============================================================================

RECIPES: Dict[str, ReportRecipe] = {
    # -------------------------------------------------------------------------
    # VENDAS
    # -------------------------------------------------------------------------
    "vendas": ReportRecipe(
        nome="vendas",
        descricao="Relatorio completo de vendas",
        modulo="vendas",
        kpis_inclusos=[
            "faturamento_total",
            "ticket_medio",
            "qtd_pedidos",
            "vendas_por_vendedor",
            "vendas_por_cliente",
            "taxa_desconto",
            "crescimento_mom",
            "top_produtos",
            "curva_abc_clientes",
        ],
        template="daily.html",
        filtros_suportados=["periodo", "cliente", "vendedor", "empresa", "produto"],
        periodo_padrao="30d"
    ),
    "vendas_diario": ReportRecipe(
        nome="vendas_diario",
        descricao="Vendas do dia",
        modulo="vendas",
        kpis_inclusos=[
            "faturamento_total",
            "ticket_medio",
            "qtd_pedidos",
            "vendas_por_vendedor",
        ],
        template="daily.html",
        filtros_suportados=["empresa"],
        periodo_padrao="1d"
    ),
    "vendas_semanal": ReportRecipe(
        nome="vendas_semanal",
        descricao="Vendas da semana",
        modulo="vendas",
        kpis_inclusos=[
            "faturamento_total",
            "ticket_medio",
            "qtd_pedidos",
            "vendas_por_vendedor",
            "vendas_por_cliente",
            "top_produtos",
        ],
        template="daily.html",
        filtros_suportados=["empresa", "vendedor"],
        periodo_padrao="7d"
    ),
    "vendas_mensal": ReportRecipe(
        nome="vendas_mensal",
        descricao="Comparativo mensal de vendas",
        modulo="vendas",
        kpis_inclusos=[
            "faturamento_total",
            "crescimento_mom",
            "vendas_por_cliente",
            "curva_abc_clientes",
        ],
        template="daily.html",
        filtros_suportados=["empresa", "vendedor"],
        periodo_padrao="6m"
    ),

    # -------------------------------------------------------------------------
    # COMPRAS
    # -------------------------------------------------------------------------
    "compras": ReportRecipe(
        nome="compras",
        descricao="Relatorio completo de compras",
        modulo="compras",
        kpis_inclusos=[
            "volume_compras",
            "custo_medio_produto",
            "lead_time_fornecedor",
            "pedidos_pendentes",
            "top_fornecedores",
        ],
        template="daily.html",
        filtros_suportados=["periodo", "fornecedor", "empresa"],
        periodo_padrao="30d"
    ),
    "compras_pendentes": ReportRecipe(
        nome="compras_pendentes",
        descricao="Pedidos de compra pendentes",
        modulo="compras",
        kpis_inclusos=[
            "pedidos_pendentes",
            "taxa_conferencia_wms",
        ],
        template="daily.html",
        filtros_suportados=["fornecedor", "empresa"],
        periodo_padrao="90d"
    ),

    # -------------------------------------------------------------------------
    # ESTOQUE
    # -------------------------------------------------------------------------
    "estoque": ReportRecipe(
        nome="estoque",
        descricao="Relatorio completo de estoque",
        modulo="estoque",
        kpis_inclusos=[
            "estoque_total_valor",
            "estoque_total_unidades",
            "giro_estoque",
            "produtos_sem_estoque",
            "cobertura_estoque",
            "curva_abc_estoque",
        ],
        template="daily.html",
        filtros_suportados=["empresa", "produto", "local"],
        periodo_padrao=None  # Estoque e snapshot, nao tem periodo
    ),
    "estoque_critico": ReportRecipe(
        nome="estoque_critico",
        descricao="Produtos com estoque critico",
        modulo="estoque",
        kpis_inclusos=[
            "produtos_sem_estoque",
            "estoque_por_empresa",
        ],
        template="daily.html",
        filtros_suportados=["empresa"],
        periodo_padrao=None
    ),
}


# =============================================================================
# CLASSE ANALISTA
# =============================================================================

class Analista:
    """
    Interface simplificada para o Agente Analista.

    Gera relatorios inteligentes baseados em receitas pre-definidas.
    Cada receita sabe quais KPIs calcular, qual template usar e
    quais filtros aceitar.
    """

    # Mapeamento de modulos para calculadores de KPI
    KPI_CLASSES = {
        "vendas": VendasKPI,
        "compras": ComprasKPI,
        "estoque": EstoqueKPI,
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

    def __init__(self, salvar_disco: bool = True):
        """
        Inicializa o Analista.

        Args:
            salvar_disco: Se True, salva relatorios em disco automaticamente
        """
        self.salvar_disco = salvar_disco
        self.loader = AnalystDataLoader()
        self.generator = ReportGenerator()
        self._output_dir = Path(ANALYST_CONFIG.get("output_dir", "output/reports"))

    def relatorio(
        self,
        tipo: str,
        **filtros
    ) -> ReportResult:
        """
        Gera relatorio inteligente baseado no tipo.

        O tipo pode ser:
        - Um nome de receita: "vendas", "vendas_diario", "estoque_critico", etc.
        - Um nome de modulo: "vendas", "compras", "estoque" (usa receita padrao)

        Args:
            tipo: Nome do relatorio ou modulo
            **filtros: Filtros dinamicos:
                - periodo: "7d", "30d", "90d", etc.
                - cliente: Nome ou codigo
                - vendedor: Codigo
                - fornecedor: Codigo
                - empresa: Codigo
                - produto: Nome ou codigo

        Returns:
            ReportResult com HTML, KPIs e metadados

        Exemplos:
            # Relatorio padrao de vendas (ultimos 30 dias)
            result = analista.relatorio("vendas")

            # Vendas de um cliente especifico
            result = analista.relatorio("vendas", cliente="AUTO PECAS XYZ")

            # Vendas do dia
            result = analista.relatorio("vendas_diario")

            # Estoque critico
            result = analista.relatorio("estoque_critico")
        """
        tipo_lower = tipo.lower()

        # Buscar receita
        recipe = RECIPES.get(tipo_lower)
        if not recipe:
            # Tentar usar tipo como modulo (receita padrao)
            if tipo_lower in self.KPI_CLASSES:
                recipe = RECIPES.get(tipo_lower)
            else:
                return self._error_result(
                    tipo_lower,
                    f"Tipo de relatorio '{tipo}' nao existe. Disponiveis: {self.listar_relatorios()}"
                )

        logger.info(f"[{tipo_lower}] Gerando relatorio: {recipe.descricao}")

        # Extrair periodo dos filtros ou usar padrao da receita
        periodo = filtros.pop("periodo", recipe.periodo_padrao)
        data_inicio, data_fim = self._calcular_periodo(periodo)

        try:
            # 1. Carregar dados
            df = self.loader.load(
                entity=recipe.modulo,
                data_inicio=data_inicio,
                data_fim=data_fim
            )

            if df.empty:
                return self._error_result(
                    tipo_lower,
                    "Nenhum dado encontrado para o periodo/filtros especificados"
                )

            registros_originais = len(df)

            # 2. Aplicar filtros ao DataFrame
            df = self._aplicar_filtros(df, filtros)

            if df.empty:
                return self._error_result(
                    tipo_lower,
                    f"Nenhum dado apos aplicar filtros: {filtros}"
                )

            logger.info(f"[{tipo_lower}] {len(df)} registros apos filtros (de {registros_originais})")

            # 3. Calcular KPIs
            kpi_class = self.KPI_CLASSES[recipe.modulo]()
            kpis = kpi_class.calculate_all(df, data_inicio=data_inicio, data_fim=data_fim)

            # 4. Gerar HTML
            titulo = f"{recipe.descricao} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

            output_path = None
            if self.salvar_disco:
                self._output_dir.mkdir(parents=True, exist_ok=True)
                filename = f"{tipo_lower}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                output_path = str(self._output_dir / filename)

            html = self.generator.generate(
                kpis={recipe.modulo: kpis},
                template=recipe.template,
                output_path=output_path,
                title=titulo
            )

            result = ReportResult(
                success=True,
                tipo=tipo_lower,
                titulo=titulo,
                html=html,
                caminho_arquivo=output_path,
                kpis={recipe.modulo: kpis},
                filtros_aplicados=filtros,
                periodo=(data_inicio or "", data_fim or ""),
                registros_analisados=len(df),
                timestamp=datetime.now()
            )

            logger.info(str(result))
            return result

        except Exception as e:
            logger.error(f"[{tipo_lower}] Erro ao gerar relatorio: {e}")
            return self._error_result(tipo_lower, str(e))

    def kpis(
        self,
        modulo: str,
        **filtros
    ) -> Dict[str, Any]:
        """
        Calcula apenas KPIs sem gerar HTML.

        Util quando voce quer apenas os numeros, sem relatorio visual.

        Args:
            modulo: "vendas", "compras" ou "estoque"
            **filtros: Filtros de dados (periodo, cliente, etc.)

        Returns:
            Dict estruturado com KPIs calculados

        Exemplos:
            kpis = analista.kpis("vendas", periodo="7d")
            print(f"Faturamento: {kpis['faturamento_total']['formatted']}")
            print(f"Ticket medio: {kpis['ticket_medio']['formatted']}")
        """
        modulo_lower = modulo.lower()

        if modulo_lower not in self.KPI_CLASSES:
            return {
                "error": f"Modulo '{modulo}' nao existe. Disponiveis: {list(self.KPI_CLASSES.keys())}"
            }

        # Extrair periodo
        periodo = filtros.pop("periodo", "30d")
        data_inicio, data_fim = self._calcular_periodo(periodo)

        try:
            # Carregar dados
            df = self.loader.load(
                entity=modulo_lower,
                data_inicio=data_inicio,
                data_fim=data_fim
            )

            if df.empty:
                return {"error": "Nenhum dado encontrado"}

            # Aplicar filtros
            df = self._aplicar_filtros(df, filtros)

            if df.empty:
                return {"error": "Nenhum dado apos aplicar filtros"}

            # Calcular KPIs
            kpi_class = self.KPI_CLASSES[modulo_lower]()
            result = kpi_class.calculate_all(df, data_inicio=data_inicio, data_fim=data_fim)

            # Adicionar metadata
            result["_metadata"] = {
                "modulo": modulo_lower,
                "periodo": periodo,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "registros": len(df),
                "filtros": filtros,
                "calculado_em": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"[{modulo_lower}] Erro ao calcular KPIs: {e}")
            return {"error": str(e)}

    def listar_relatorios(self) -> List[str]:
        """
        Lista tipos de relatorios disponiveis.

        Returns:
            Lista de nomes de relatorios
        """
        return list(RECIPES.keys())

    def descrever_relatorio(self, tipo: str) -> Optional[Dict[str, Any]]:
        """
        Retorna detalhes de um tipo de relatorio.

        Args:
            tipo: Nome do relatorio

        Returns:
            Dict com descricao, KPIs inclusos, filtros suportados, etc.
        """
        recipe = RECIPES.get(tipo.lower())
        if not recipe:
            return None

        return {
            "nome": recipe.nome,
            "descricao": recipe.descricao,
            "modulo": recipe.modulo,
            "kpis": recipe.kpis_inclusos,
            "filtros_suportados": recipe.filtros_suportados,
            "periodo_padrao": recipe.periodo_padrao,
        }

    def listar_modulos(self) -> List[str]:
        """
        Lista modulos de KPIs disponiveis.

        Returns:
            Lista de nomes de modulos
        """
        return list(self.KPI_CLASSES.keys())

    # -------------------------------------------------------------------------
    # Metodos Privados
    # -------------------------------------------------------------------------

    def _calcular_periodo(self, periodo: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Calcula datas de inicio e fim baseado no periodo."""
        if not periodo:
            return None, None

        delta = self.PERIODOS.get(periodo.lower())
        if not delta:
            logger.warning(f"Periodo '{periodo}' invalido. Disponiveis: {list(self.PERIODOS.keys())}")
            return None, None

        fim = datetime.now()
        inicio = fim - delta

        return inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")

    def _aplicar_filtros(self, df: pd.DataFrame, filtros: Dict[str, Any]) -> pd.DataFrame:
        """
        Aplica filtros dinamicos ao DataFrame.

        Suporta filtros por nome (busca parcial) ou codigo (match exato).
        """
        if not filtros:
            return df

        # Mapeamento de filtros para colunas possiveis
        FILTRO_COLUNAS = {
            "cliente": ["CODPARC", "NOMEPARC", "RAZAOSOCIAL"],
            "vendedor": ["CODVEND", "APELIDO_VEND", "NOMEVEND"],
            "fornecedor": ["CODPARC", "NOMEPARC"],
            "empresa": ["CODEMP"],
            "produto": ["CODPROD", "DESCRPROD", "REFERENCIA"],
            "local": ["CODLOCAL", "DESCR_LOCAL"],
        }

        for filtro, valor in filtros.items():
            filtro_lower = filtro.lower()
            colunas = FILTRO_COLUNAS.get(filtro_lower, [])

            if not colunas:
                logger.warning(f"Filtro '{filtro}' nao reconhecido, ignorando")
                continue

            filtro_aplicado = False

            for col in colunas:
                if col not in df.columns:
                    continue

                # Se valor e numerico, filtrar por igualdade
                if isinstance(valor, (int, float)):
                    df = df[df[col] == valor]
                    filtro_aplicado = True
                    logger.debug(f"Filtro {filtro}={valor} aplicado na coluna {col} (exato)")
                    break

                # Se string, tentar match parcial (case insensitive)
                elif isinstance(valor, str):
                    if df[col].dtype == "object":
                        mask = df[col].str.contains(valor, case=False, na=False)
                        df = df[mask]
                        filtro_aplicado = True
                        logger.debug(f"Filtro {filtro}='{valor}' aplicado na coluna {col} (parcial)")
                        break
                    else:
                        # Coluna nao e string, tentar conversao
                        try:
                            valor_num = int(valor)
                            df = df[df[col] == valor_num]
                            filtro_aplicado = True
                            break
                        except ValueError:
                            continue

            if not filtro_aplicado:
                logger.warning(f"Filtro '{filtro}' nao pode ser aplicado (coluna nao encontrada)")

        return df

    def _error_result(self, tipo: str, erro: str) -> ReportResult:
        """Cria resultado de erro padronizado."""
        result = ReportResult(
            success=False,
            tipo=tipo,
            titulo="",
            erros=[erro]
        )
        logger.error(str(result))
        return result
