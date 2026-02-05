# -*- coding: utf-8 -*-
"""Módulos compartilhados entre agentes."""

from .rag import DocumentRetriever, DocumentStore, search_documentation, get_embeddings

__all__ = [
    "DocumentRetriever",
    "DocumentStore",
    "search_documentation",
    "get_embeddings",
]
