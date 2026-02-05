# -*- coding: utf-8 -*-
"""
Script para Chat com a IA do Data Hub

Uso:
    python scripts/chat_ia.py

Ou para pergunta direta:
    python scripts/chat_ia.py "Qual a previsão de vendas do produto 261301?"
"""

import sys
import os
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    os.system('chcp 65001 > nul 2>&1')

# Adicionar src ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import logging

# Configurar logging
logging.basicConfig(
    level=logging.WARNING,  # Reduzir verbosidade
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    """Função principal."""

    print("\n🚀 Iniciando Data Hub IA...")

    try:
        from src.agents.orchestrator import OrchestratorAgent
        agent = OrchestratorAgent()
        print("✅ Agente inicializado com sucesso!\n")

    except ValueError as e:
        print(f"\n❌ Erro de configuração: {e}")
        print("\n📝 Configure sua API key do Groq:")
        print("   1. Acesse https://console.groq.com/keys")
        print("   2. Crie uma API key")
        print("   3. Adicione ao arquivo .env: GROQ_API_KEY=sua_chave")
        return

    except Exception as e:
        print(f"\n❌ Erro ao inicializar: {e}")
        return

    # Se recebeu pergunta como argumento
    if len(sys.argv) > 1:
        pergunta = " ".join(sys.argv[1:])
        print(f"Pergunta: {pergunta}")
        print("\n🤔 Processando...")
        resposta = agent.ask(pergunta)
        print(f"\n🤖 Resposta:\n{resposta}")
        return

    # Modo interativo
    agent.chat()


if __name__ == "__main__":
    main()
