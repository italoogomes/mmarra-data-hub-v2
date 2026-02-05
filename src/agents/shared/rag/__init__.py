# -*- coding: utf-8 -*-
"""
RAG (Retrieval Augmented Generation) para os Agentes

Permite que os agentes busquem informacoes na documentacao
do projeto antes de responder.
"""

from .embeddings import get_embeddings
from .vectorstore import DocumentStore
from .retriever import DocumentRetriever, search_documentation, get_retriever

__all__ = [
    "get_embeddings",
    "DocumentStore",
    "DocumentRetriever",
    "search_documentation",
    "get_retriever",
]
