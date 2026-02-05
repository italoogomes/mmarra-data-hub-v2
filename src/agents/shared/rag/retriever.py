# -*- coding: utf-8 -*-
"""
Retriever para RAG - Interface de Busca para Agentes

Fornece uma interface simples para os agentes buscarem
informacoes na documentacao do projeto.
"""

import logging
from typing import List, Optional, Dict, Any
from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.tools import tool

from .vectorstore import DocumentStore

logger = logging.getLogger(__name__)

# Instancia global do retriever
_retriever_instance: Optional["DocumentRetriever"] = None


class DocumentRetriever:
    """
    Interface de busca para os agentes.

    Uso:
        retriever = DocumentRetriever()
        contexto = retriever.get_context("como consultar estoque")
        # contexto eh uma string formatada com os documentos relevantes
    """

    def __init__(self, auto_build: bool = True):
        """
        Inicializa o retriever.

        Args:
            auto_build: Se True, constroi o indice se nao existir
        """
        self.store = DocumentStore()

        # Tentar carregar indice existente
        if not self.store.load_index():
            if auto_build:
                logger.info("Indice nao encontrado. Construindo...")
                self.store.build_index()
            else:
                logger.warning("Indice nao encontrado e auto_build=False")

    def search(
        self,
        query: str,
        k: int = 5,
        min_score: float = 0.0
    ) -> List[Document]:
        """
        Busca documentos relevantes.

        Args:
            query: Texto de busca
            k: Numero maximo de resultados
            min_score: Score minimo (0.0 a 1.0, maior = mais similar)

        Returns:
            Lista de documentos relevantes
        """
        results = self.store.search_with_scores(query, k=k)

        # Filtrar por score minimo (FAISS retorna distancia, menor = melhor)
        # Convertemos para score: score = 1 / (1 + distancia)
        filtered = []
        for doc, distance in results:
            score = 1 / (1 + distance)
            if score >= min_score:
                doc.metadata["relevance_score"] = round(score, 3)
                filtered.append(doc)

        return filtered

    def get_context(
        self,
        query: str,
        k: int = 5,
        include_metadata: bool = True
    ) -> str:
        """
        Retorna contexto formatado para o LLM.

        Args:
            query: Texto de busca
            k: Numero de documentos
            include_metadata: Incluir informacoes de fonte

        Returns:
            String formatada com o contexto relevante
        """
        docs = self.search(query, k=k)

        if not docs:
            return "Nenhum documento relevante encontrado na base de conhecimento."

        context_parts = []
        for i, doc in enumerate(docs, 1):
            if include_metadata:
                source = doc.metadata.get("file_path", "Desconhecido")
                source_type = doc.metadata.get("source_type", "")
                score = doc.metadata.get("relevance_score", 0)

                header = f"[Documento {i}] Fonte: {source} ({source_type}) - Relevancia: {score}"
                context_parts.append(f"{header}\n{doc.page_content}")
            else:
                context_parts.append(doc.page_content)

        return "\n\n---\n\n".join(context_parts)

    def get_relevant_info(
        self,
        query: str,
        k: int = 3
    ) -> Dict[str, Any]:
        """
        Retorna informacoes estruturadas para tools.

        Args:
            query: Texto de busca
            k: Numero de documentos

        Returns:
            Dict com documentos e metadados
        """
        docs = self.search(query, k=k)

        return {
            "query": query,
            "found": len(docs),
            "documents": [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("file_path", ""),
                    "type": doc.metadata.get("source_type", ""),
                    "score": doc.metadata.get("relevance_score", 0)
                }
                for doc in docs
            ]
        }

    def rebuild_index(self) -> int:
        """Reconstroi o indice do zero."""
        return self.store.build_index(force=True)


def get_retriever() -> DocumentRetriever:
    """Retorna instancia singleton do retriever."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = DocumentRetriever()
    return _retriever_instance


# =============================================================================
# TOOL PARA OS AGENTES
# =============================================================================

@tool
def search_documentation(query: str) -> str:
    """
    Busca informacoes na documentacao do projeto.

    Use esta ferramenta quando precisar de informacoes sobre:
    - Estrutura de tabelas do Sankhya (campos, tipos, relacionamentos)
    - Bugs e problemas conhecidos
    - Queries SQL uteis
    - Como fazer operacoes especificas
    - Documentacao do WMS
    - Descobertas e investigacoes anteriores

    Args:
        query: O que voce quer saber (em portugues)

    Returns:
        Contexto relevante da documentacao do projeto
    """
    retriever = get_retriever()
    return retriever.get_context(query, k=5)


# =============================================================================
# TESTES
# =============================================================================

def test_retriever():
    """Testa o retriever com perguntas de exemplo."""
    print("=" * 60)
    print("TESTE DO RETRIEVER RAG")
    print("=" * 60)

    retriever = DocumentRetriever()

    perguntas = [
        "O que significa o campo TIPMOV?",
        "Quais problemas ja encontramos no WMS?",
        "Como consultar pedidos de compra pendentes?",
    ]

    for pergunta in perguntas:
        print(f"\n{'='*60}")
        print(f"PERGUNTA: {pergunta}")
        print("=" * 60)

        contexto = retriever.get_context(pergunta, k=3)
        print(contexto[:1000])
        if len(contexto) > 1000:
            print(f"\n... (mais {len(contexto) - 1000} caracteres)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_retriever()
