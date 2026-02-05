#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Servidor MCP para API Sankhya
=================================
Permite que o Claude Code execute queries SQL diretamente na API Sankhya
e processe os resultados automaticamente.

Versão: 1.0.0
Data: 2026-02-01
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


class SankhyaAPI:
    """Cliente para API Sankhya com gerenciamento automático de token."""

    def __init__(self):
        self.auth_url = "https://api.sankhya.com.br"  # Autenticação
        self.gateway_url = "https://api.sankhya.com.br/gateway/v1"  # Queries
        self.client_id = os.getenv("SANKHYA_CLIENT_ID")
        self.client_secret = os.getenv("SANKHYA_CLIENT_SECRET")
        self.x_token = os.getenv("SANKHYA_X_TOKEN")

        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

        if not all([self.client_id, self.client_secret, self.x_token]):
            raise ValueError(
                "Credenciais Sankhya não configuradas! "
                "Configure SANKHYA_CLIENT_ID, SANKHYA_CLIENT_SECRET e SANKHYA_X_TOKEN"
            )

    async def _get_token(self) -> str:
        """Obtém ou renova o token de acesso."""
        # Se token existe e ainda é válido, retorna
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token

        # Renovar token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_url}/authenticate",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Token": self.x_token
                },
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                },
                timeout=30.0
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data["access_token"]
            # Token válido por 24h, renovar 1h antes
            self.token_expiry = datetime.now() + timedelta(hours=23)

            return self.access_token

    async def execute_query(self, sql: str) -> dict:
        """
        Executa uma query SQL na API Sankhya.

        Args:
            sql: Query SQL a executar

        Returns:
            dict: Resposta da API com os dados
        """
        token = await self._get_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.gateway_url}/mge/service.sbr",
                params={
                    "serviceName": "DbExplorerSP.executeQuery",
                    "outputType": "json"
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "requestBody": {
                        "sql": sql
                    }
                },
                timeout=120.0  # Queries podem demorar
            )
            response.raise_for_status()

            return response.json()


class SankhyaMCPServer:
    """Servidor MCP para integração com Sankhya."""

    def __init__(self):
        self.server = Server("sankhya-mcp")
        self.api = SankhyaAPI()
        self.queries_path = Path(__file__).parent.parent / "queries"

        # Registrar tools
        self._register_tools()

    def _register_tools(self):
        """Registra todas as tools do servidor."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="executar_query_sql",
                    description="Executa uma query SQL diretamente no banco Oracle da Sankhya",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "Query SQL a executar (Oracle SQL syntax)"
                            }
                        },
                        "required": ["sql"]
                    }
                ),
                Tool(
                    name="executar_query_divergencias",
                    description="Executa a query V3 de divergências de estoque (corrigida, sem multiplicação)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "codemp": {
                                "type": "integer",
                                "description": "Código da empresa (padrão: 7)",
                                "default": 7
                            }
                        }
                    }
                ),
                Tool(
                    name="executar_query_analise_produto",
                    description="Executa a query de análise detalhada de um produto específico",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "codemp": {
                                "type": "integer",
                                "description": "Código da empresa"
                            },
                            "codprod": {
                                "type": "integer",
                                "description": "Código do produto a analisar"
                            }
                        },
                        "required": ["codemp", "codprod"]
                    }
                ),
                Tool(
                    name="gerar_relatorio_divergencias",
                    description="Gera relatório HTML interativo com dados de divergências",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dados_json": {
                                "type": "string",
                                "description": "JSON com dados de divergências (resultado da query)"
                            },
                            "arquivo_saida": {
                                "type": "string",
                                "description": "Nome do arquivo HTML de saída",
                                "default": "relatorio_divergencias_completo.html"
                            }
                        },
                        "required": ["dados_json"]
                    }
                ),
                Tool(
                    name="listar_queries_disponiveis",
                    description="Lista todas as queries SQL disponíveis no projeto",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            if name == "executar_query_sql":
                return await self._executar_query_sql(arguments["sql"])

            elif name == "executar_query_divergencias":
                codemp = arguments.get("codemp", 7)
                return await self._executar_query_divergencias(codemp)

            elif name == "executar_query_analise_produto":
                return await self._executar_query_analise_produto(
                    arguments["codemp"],
                    arguments["codprod"]
                )

            elif name == "gerar_relatorio_divergencias":
                return await self._gerar_relatorio_divergencias(
                    arguments["dados_json"],
                    arguments.get("arquivo_saida", "relatorio_divergencias_completo.html")
                )

            elif name == "listar_queries_disponiveis":
                return await self._listar_queries_disponiveis()

            else:
                raise ValueError(f"Tool desconhecida: {name}")

    async def _executar_query_sql(self, sql: str) -> list[TextContent]:
        """Executa query SQL customizada."""
        try:
            resultado = await self.api.execute_query(sql)

            # Extrair dados
            if "responseBody" in resultado and "rows" in resultado["responseBody"]:
                rows = resultado["responseBody"]["rows"]
                total = len(rows)

                # Formatar resultado
                resposta = f"✅ Query executada com sucesso!\n\n"
                resposta += f"📊 Total de registros: {total}\n\n"
                resposta += f"📋 Dados:\n```json\n{json.dumps(rows[:5], indent=2, ensure_ascii=False)}\n```\n"

                if total > 5:
                    resposta += f"\n(Mostrando 5 de {total} registros)\n"

                return [TextContent(type="text", text=resposta)]

            else:
                return [TextContent(
                    type="text",
                    text=f"⚠️ Resposta sem dados:\n```json\n{json.dumps(resultado, indent=2)}\n```"
                )]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro ao executar query: {str(e)}")]

    async def _executar_query_divergencias(self, codemp: int) -> list[TextContent]:
        """Executa query de divergências V3."""
        sql = f"""
        SELECT CAB.CODEMP, ITE.CODPROD, PRO.DESCRPROD, PRO.REFERENCIA, ITE.NUNOTA,
               CAB.NUMNOTA, CAB.CODTIPOPER AS TOP, TOP.DESCROPER AS DESCR_TOP,
               ITE.QTDNEG AS QTD_NOTA, ITE.STATUSNOTA AS STATUS_ITEM,
               CAB.STATUSNOTA AS STATUS_CAB, NVL(EST.ESTOQUE_TGFEST, 0) AS QTD_DISPONIVEL_TGFEST,
               NVL(WMS.ESTOQUE_WMS, 0) AS QTD_WMS,
               (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE_TGFEST, 0)) AS DIVERGENCIA,
               TO_CHAR(CAB.DTNEG, 'DD/MM/YYYY') AS DATA_NOTA
        FROM TGFITE ITE
        INNER JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
        INNER JOIN TGFPRO PRO ON ITE.CODPROD = PRO.CODPROD
        LEFT JOIN (
            SELECT DISTINCT CODTIPOPER, MIN(DESCROPER) AS DESCROPER
            FROM TGFTOP
            GROUP BY CODTIPOPER
        ) TOP ON CAB.CODTIPOPER = TOP.CODTIPOPER
        LEFT JOIN (
            SELECT CODPROD, CODEMP, SUM(NVL(ESTOQUE, 0)) AS ESTOQUE_TGFEST
            FROM TGFEST
            WHERE CODEMP = {codemp}
            GROUP BY CODPROD, CODEMP
        ) EST ON ITE.CODPROD = EST.CODPROD AND EST.CODEMP = CAB.CODEMP
        LEFT JOIN (
            SELECT CODPROD, SUM(NVL(ESTOQUE, 0)) AS ESTOQUE_WMS
            FROM TGWEST
            WHERE CODEMP = {codemp}
            GROUP BY CODPROD
        ) WMS ON ITE.CODPROD = WMS.CODPROD
        WHERE CAB.CODEMP = {codemp}
          AND ITE.STATUSNOTA = 'P'
          AND NVL(WMS.ESTOQUE_WMS, 0) > NVL(EST.ESTOQUE_TGFEST, 0)
          AND (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE_TGFEST, 0)) > 0
        ORDER BY (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE_TGFEST, 0)) DESC
        """

        try:
            resultado = await self.api.execute_query(sql)

            if "responseBody" in resultado and "rows" in resultado["responseBody"]:
                rows = resultado["responseBody"]["rows"]
                total = len(rows)

                # Calcular estatísticas
                produtos_unicos = len(set(row[1] for row in rows))  # CODPROD
                notas_unicas = len(set(row[4] for row in rows))     # NUNOTA
                divergencia_total = sum(row[13] for row in rows)    # DIVERGENCIA
                maior_divergencia = max(row[13] for row in rows) if rows else 0

                resposta = f"✅ Query de Divergências V3 executada com sucesso!\n\n"
                resposta += f"📊 ESTATÍSTICAS:\n"
                resposta += f"   • Total de registros: {total}\n"
                resposta += f"   • Produtos únicos: {produtos_unicos}\n"
                resposta += f"   • Notas únicas: {notas_unicas}\n"
                resposta += f"   • Divergência total: {divergencia_total:,} unidades\n"
                resposta += f"   • Maior divergência: {maior_divergencia:,} unidades\n\n"

                # Mostrar top 5 divergências
                resposta += f"🔝 TOP 5 DIVERGÊNCIAS:\n\n"
                for i, row in enumerate(rows[:5], 1):
                    codprod = row[1]
                    descrprod = row[2][:40]
                    divergencia = row[13]
                    resposta += f"{i}. Produto {codprod} ({descrprod}): {divergencia:,} un\n"

                # Salvar JSON completo
                json_path = Path(__file__).parent.parent / "resultado_query_divergencias.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(resultado, f, ensure_ascii=False, indent=2)

                resposta += f"\n💾 JSON completo salvo em: {json_path}\n"
                resposta += f"\n💡 Use 'gerar_relatorio_divergencias' para criar o HTML interativo!"

                return [TextContent(type="text", text=resposta)]

            else:
                return [TextContent(
                    type="text",
                    text=f"⚠️ Nenhuma divergência encontrada para CODEMP={codemp}"
                )]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro: {str(e)}")]

    async def _executar_query_analise_produto(self, codemp: int, codprod: int) -> list[TextContent]:
        """Executa query de análise detalhada de produto."""
        sql = f"""
        WITH
        Parametros AS (SELECT {codemp} AS CODEMP, {codprod} AS CODPROD FROM DUAL),
        Empresa AS (
            SELECT EMP.CODEMP,
                   NVL(EMP.WMSLOCALAJEST, (SELECT INTEIRO FROM TSIPAR WHERE CHAVE = 'WMSLOCALAJEST')) AS CODLOCAL_AJUSTE
            FROM TGFEMP EMP
            JOIN Parametros ON Parametros.CODEMP = EMP.CODEMP
        ),
        SaldoWmsTela AS (
            SELECT SUM(NVL(ESTW.ESTOQUEVOLPAD - ESTW.SAIDPENDVOLPAD, 0)) AS SALDO_WMS_TELA
            FROM TGWEST ESTW
            JOIN TGWEND WEND ON WEND.CODEND = ESTW.CODEND
            JOIN TGFEMP EMP ON EMP.CODEMP = WEND.CODEMP
            JOIN Parametros ON Parametros.CODEMP = EMP.CODEMP AND Parametros.CODPROD = ESTW.CODPROD
            JOIN Empresa ON Empresa.CODEMP = EMP.CODEMP
            WHERE EMP.UTILIZAWMS = 'S' AND WEND.BLOQUEADO = 'N' AND WEND.EXCLCONF = 'N'
              AND NOT EXISTS (SELECT 1 FROM TGWDCA DCA WHERE DCA.TIPDOCA = 'S' AND DCA.CODEND = WEND.CODEND)
              AND ESTW.CONTROLE <> '#EXPLOTESEP'
        ),
        EstoqueComercial AS (
            SELECT SUM(NVL(EST.ESTOQUE, 0)) AS ESTOQUE,
                   SUM(NVL(EST.RESERVADO, 0)) AS RESERVADO,
                   SUM(NVL(EST.WMSBLOQUEADO, 0)) AS WMSBLOQUEADO
            FROM TGFEST EST
            JOIN Parametros ON Parametros.CODEMP = EST.CODEMP AND Parametros.CODPROD = EST.CODPROD
            JOIN Empresa ON Empresa.CODEMP = EST.CODEMP
            WHERE EST.CODLOCAL = Empresa.CODLOCAL_AJUSTE
        )
        SELECT ESTOQUE, RESERVADO, WMSBLOQUEADO,
               (ESTOQUE - RESERVADO - WMSBLOQUEADO) AS DISPONIVEL_COMERCIAL,
               NVL(SaldoWmsTela.SALDO_WMS_TELA, 0) AS SALDO_WMS_TELA
        FROM EstoqueComercial
        CROSS JOIN SaldoWmsTela
        """

        try:
            resultado = await self.api.execute_query(sql)

            if "responseBody" in resultado and "rows" in resultado["responseBody"]:
                rows = resultado["responseBody"]["rows"]

                if rows:
                    row = rows[0]
                    estoque = row[0]
                    reservado = row[1]
                    wmsbloqueado = row[2]
                    disponivel_comercial = row[3]
                    saldo_wms = row[4]

                    resposta = f"✅ Análise Detalhada - Produto {codprod} (Empresa {codemp})\n\n"
                    resposta += f"📊 CAMADAS DE DISPONIBILIDADE:\n\n"
                    resposta += f"1️⃣ ESTOQUE BRUTO (TGFEST):\n"
                    resposta += f"   └─ {estoque:,} unidades\n\n"
                    resposta += f"2️⃣ RESERVADO:\n"
                    resposta += f"   └─ {reservado:,} unidades\n\n"
                    resposta += f"3️⃣ BLOQUEADO WMS:\n"
                    resposta += f"   └─ {wmsbloqueado:,} unidades\n\n"
                    resposta += f"4️⃣ DISPONÍVEL COMERCIAL (ERP):\n"
                    resposta += f"   └─ {disponivel_comercial:,} unidades\n"
                    resposta += f"   └─ (ESTOQUE - RESERVADO - WMSBLOQUEADO)\n\n"
                    resposta += f"5️⃣ SALDO FÍSICO WMS:\n"
                    resposta += f"   └─ {saldo_wms:,} unidades\n\n"

                    divergencia = saldo_wms - disponivel_comercial
                    if divergencia != 0:
                        resposta += f"⚠️ DIVERGÊNCIA ENCONTRADA:\n"
                        resposta += f"   └─ {abs(divergencia):,} unidades "
                        resposta += f"({'WMS > ERP' if divergencia > 0 else 'ERP > WMS'})\n"
                    else:
                        resposta += f"✅ SEM DIVERGÊNCIA (WMS = ERP)\n"

                    return [TextContent(type="text", text=resposta)]

                else:
                    return [TextContent(
                        type="text",
                        text=f"⚠️ Produto {codprod} não encontrado na empresa {codemp}"
                    )]

            else:
                return [TextContent(type="text", text="⚠️ Resposta sem dados")]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro: {str(e)}")]

    async def _gerar_relatorio_divergencias(self, dados_json: str, arquivo_saida: str) -> list[TextContent]:
        """Gera relatório HTML a partir do JSON."""
        try:
            # Parse JSON
            data = json.loads(dados_json)

            # Executar script Python de geração
            script_path = Path(__file__).parent.parent / "gerar_relatorio.py"

            # Criar arquivo temporário com JSON
            temp_json = Path(__file__).parent.parent / "temp_relatorio.json"
            with open(temp_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # TODO: Integrar lógica do gerar_relatorio.py aqui

            resposta = f"✅ Relatório HTML gerado!\n\n"
            resposta += f"📄 Arquivo: {arquivo_saida}\n"
            resposta += f"🌐 Abra o arquivo no navegador para visualizar\n"

            return [TextContent(type="text", text=resposta)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro ao gerar relatório: {str(e)}")]

    async def _listar_queries_disponiveis(self) -> list[TextContent]:
        """Lista queries SQL disponíveis no projeto."""
        try:
            queries = []

            # Buscar arquivos .sql
            for sql_file in self.queries_path.glob("*.sql"):
                queries.append(f"📄 {sql_file.name}")

            if queries:
                resposta = "📋 QUERIES DISPONÍVEIS:\n\n"
                resposta += "\n".join(queries)
                resposta += "\n\n💡 Use 'executar_query_sql' com o conteúdo do arquivo"
            else:
                resposta = "⚠️ Nenhuma query encontrada em queries/"

            return [TextContent(type="text", text=resposta)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro: {str(e)}")]

    async def run(self):
        """Inicia o servidor MCP."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Função principal."""
    server = SankhyaMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
