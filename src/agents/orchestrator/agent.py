# -*- coding: utf-8 -*-
"""
Agente Orquestrador - O Cérebro do Data Hub

Este é o agente principal que:
1. Recebe perguntas dos usuários
2. Decide qual ferramenta/agente usar
3. Coordena as respostas
4. Responde em linguagem natural

Uso:
    from src.agents.orchestrator import OrchestratorAgent

    agent = OrchestratorAgent()
    resposta = agent.ask("Qual a previsão de vendas do produto 261301?")
"""

import logging
from typing import Optional, Dict, Any

from ..base import BaseAgent
from ..llm.tools import forecast_demand, get_kpis
from ..shared.rag import DocumentRetriever, search_documentation

logger = logging.getLogger(__name__)

# Prompt do Orquestrador
ORCHESTRATOR_PROMPT = """Você é o Orquestrador do Data Hub da MMarra Distribuidora.

SOBRE A EMPRESA:
- Distribuidora de autopeças para caminhões e carretas
- Trabalha com milhares de SKUs (peças)
- Precisa gerenciar estoque, vendas e compras
- Usa Sankhya ERP como sistema principal

SEU TRABALHO:
- Responder perguntas sobre o negócio
- Usar ferramentas para obter dados quando necessário
- BUSCAR NA DOCUMENTAÇÃO quando precisar de informações técnicas
- Explicar resultados de forma clara em português

FERRAMENTAS DISPONÍVEIS:

1. search_documentation(query) - BUSCA NA BASE DE CONHECIMENTO
   - Use PRIMEIRO quando precisar de informações sobre:
     * Estrutura de tabelas do Sankhya (campos, tipos, relacionamentos)
     * Significado de campos (ex: TIPMOV, CODTIPOPER)
     * Bugs e problemas conhecidos
     * Queries SQL úteis
     * Documentação do WMS
     * Como fazer operações específicas
   - query: o que você quer saber (em português)

2. forecast_demand(codprod, periods) - Previsão de vendas de um produto
   - Use quando perguntarem sobre previsão, demanda futura, vendas previstas
   - codprod: código do produto (número)
   - periods: dias para prever (padrão 30)

3. get_kpis(modulo, periodo) - Métricas e indicadores
   - Use quando perguntarem sobre faturamento, margem, KPIs
   - modulo: "vendas", "compras" ou "estoque"
   - periodo: "mes_atual", "mes_anterior" ou "ano"

REGRAS:
- Sempre responda em português brasileiro
- Use search_documentation PRIMEIRO para perguntas técnicas
- Use as outras ferramentas quando precisar de dados específicos
- Explique os resultados de forma clara e objetiva
- Se não souber algo, diga que não tem a informação
- Não invente dados - use apenas o que as ferramentas retornarem

EXEMPLOS:
- "O que significa TIPMOV?" → Use search_documentation("significado campo TIPMOV")
- "Quais bugs existem no WMS?" → Use search_documentation("bugs problemas WMS")
- "Qual a previsão de vendas do produto 261301?" → Use forecast_demand
- "Qual o faturamento do mês?" → Use get_kpis(modulo="vendas")
"""


class OrchestratorAgent(BaseAgent):
    """
    Agente Orquestrador do Data Hub.

    Coordena os outros agentes e responde usuários.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.3
    ):
        """
        Inicializa o Orquestrador.

        Args:
            model: Modelo LLM (default: llama-3.1-70b-versatile)
            temperature: Temperatura do modelo
        """
        # Configurar tools (RAG primeiro para priorizar busca na documentação)
        tools = [search_documentation, forecast_demand, get_kpis]

        super().__init__(
            name="Orquestrador",
            system_prompt=ORCHESTRATOR_PROMPT,
            tools=tools,
            model=model,
            temperature=temperature
        )

        logger.info("Orquestrador inicializado com RAG, previsão e KPIs")

    def ask(self, question: str) -> str:
        """
        Faz uma pergunta ao Orquestrador.

        Args:
            question: Pergunta em linguagem natural

        Returns:
            Resposta do agente
        """
        return self.run(question)

    def chat(self):
        """
        Inicia um chat interativo no terminal.

        Use Ctrl+C para sair.
        """
        print("\n" + "=" * 60)
        print("🤖 Data Hub - Chat com IA")
        print("=" * 60)
        print("Digite sua pergunta ou 'sair' para encerrar.\n")

        while True:
            try:
                pergunta = input("Você: ").strip()

                if not pergunta:
                    continue

                if pergunta.lower() in ["sair", "exit", "quit"]:
                    print("\n👋 Até logo!")
                    break

                print("\n🤔 Pensando...")
                resposta = self.ask(pergunta)
                print(f"\n🤖 Assistente: {resposta}\n")

            except KeyboardInterrupt:
                print("\n\n👋 Chat encerrado.")
                break
            except Exception as e:
                print(f"\n❌ Erro: {e}\n")


# Função de conveniência
def create_orchestrator() -> OrchestratorAgent:
    """Cria e retorna uma instância do Orquestrador."""
    return OrchestratorAgent()
