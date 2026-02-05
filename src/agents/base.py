# -*- coding: utf-8 -*-
"""
Classe Base para Agentes Autônomos

Todos os agentes (Engenheiro, Analista, Cientista, Orquestrador) herdam desta classe.

Características:
- Usa Groq como provider de LLM
- Suporta ferramentas (tools)
- Tem memória de conversação
"""

import os
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Classe base para todos os agentes autônomos.

    Uso:
        agent = BaseAgent(
            name="Engenheiro",
            system_prompt="Você é o Engenheiro de Dados...",
            tools=[tool1, tool2]
        )
        resposta = agent.run("Extraia os dados de vendas")
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: Optional[List[BaseTool]] = None,
        model: Optional[str] = None,
        temperature: float = 0.1
    ):
        """
        Inicializa o agente.

        Args:
            name: Nome do agente
            system_prompt: Prompt de sistema que define a personalidade
            tools: Lista de ferramentas disponíveis
            model: Modelo LLM (default: llama-3.1-70b-versatile)
            temperature: Temperatura do modelo (0.0 = determinístico, 1.0 = criativo)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.temperature = temperature

        # Configurar modelo
        self.model = model or os.getenv("LLM_MODEL", "llama-3.1-70b-versatile")

        # Verificar API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY não configurada. "
                "Adicione ao arquivo .env: GROQ_API_KEY=sua_chave"
            )

        # Criar LLM
        self.llm = ChatGroq(
            model=self.model,
            temperature=self.temperature,
            api_key=api_key
        )

        # Bind tools se houver
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

        # Memória de conversação
        self.memory: List[Dict[str, Any]] = []

        logger.info(f"Agente '{self.name}' inicializado com modelo {self.model}")

    def _get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """Encontra uma tool pelo nome."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def run(self, task: str) -> str:
        """
        Executa uma tarefa.

        Args:
            task: Descrição da tarefa a executar

        Returns:
            Resposta do agente
        """
        # Montar mensagens
        messages = [
            SystemMessage(content=self.system_prompt),
        ]

        # Adicionar histórico
        for msg in self.memory[-10:]:  # Últimas 10 mensagens
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        # Adicionar tarefa atual
        messages.append(HumanMessage(content=task))

        try:
            # Loop para processar tool calls
            max_iterations = 5
            for _ in range(max_iterations):
                # Chamar LLM
                response = self.llm_with_tools.invoke(messages)

                # Verificar se há tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    # Adicionar resposta do AI às mensagens
                    messages.append(response)

                    # Executar cada tool call
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        tool_id = tool_call["id"]

                        logger.info(f"Executando tool: {tool_name}({tool_args})")

                        # Encontrar e executar a tool
                        tool = self._get_tool_by_name(tool_name)
                        if tool:
                            try:
                                tool_result = tool.invoke(tool_args)
                                logger.info(f"Resultado da tool {tool_name}: {tool_result}")
                            except Exception as e:
                                tool_result = {"error": str(e)}
                                logger.error(f"Erro na tool {tool_name}: {e}")
                        else:
                            tool_result = {"error": f"Tool '{tool_name}' não encontrada"}

                        # Adicionar resultado da tool às mensagens
                        messages.append(ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_id
                        ))
                else:
                    # Sem tool calls - temos a resposta final
                    break

            # Extrair conteúdo final
            if hasattr(response, 'content'):
                result = response.content
            else:
                result = str(response)

            # Salvar na memória
            self.memory.append({"role": "user", "content": task})
            self.memory.append({"role": "assistant", "content": result})

            return result

        except Exception as e:
            logger.error(f"Erro ao executar tarefa: {e}")
            raise

    def clear_memory(self):
        """Limpa a memória de conversação."""
        self.memory = []
        logger.info(f"Memória do agente '{self.name}' limpa")

    def get_state(self) -> Dict[str, Any]:
        """
        Retorna o estado atual do agente.

        Returns:
            Dict com informações do agente
        """
        return {
            "name": self.name,
            "model": self.model,
            "tools": [t.name for t in self.tools] if self.tools else [],
            "memory_size": len(self.memory),
        }
