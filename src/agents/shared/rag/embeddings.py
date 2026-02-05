# -*- coding: utf-8 -*-
"""
Configuracao de Embeddings para RAG

Versao simplificada usando TF-IDF (funciona offline).
"""

import logging
from typing import List, Optional
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class TfidfEmbeddings:
    """
    Embeddings simples usando TF-IDF.
    Funciona 100% offline, sem dependencias externas.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words=None  # Manter stopwords para PT-BR
        )
        self._fitted = False
        self._documents: List[str] = []

    def fit(self, documents: List[str]):
        """Treina o vetorizador com documentos."""
        self._documents = documents
        if documents:
            self.vectorizer.fit(documents)
            self._fitted = True
            logger.info(f"TF-IDF treinado com {len(documents)} documentos")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para lista de textos."""
        if not self._fitted:
            # Se nao treinado, treinar com os proprios textos
            self.fit(texts)

        vectors = self.vectorizer.transform(texts).toarray()
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Gera embedding para uma query."""
        if not self._fitted:
            logger.warning("Vetorizador nao treinado. Retornando vetor vazio.")
            return [0.0] * 1000

        vector = self.vectorizer.transform([text]).toarray()[0]
        return vector.tolist()


_embeddings_instance: Optional[TfidfEmbeddings] = None


def get_embeddings() -> TfidfEmbeddings:
    """Retorna instancia singleton dos embeddings."""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = TfidfEmbeddings()
        logger.info("TF-IDF Embeddings inicializado (modo offline)")
    return _embeddings_instance


def test_embeddings():
    """Testa se os embeddings estao funcionando."""
    embeddings = get_embeddings()

    # Treinar com alguns exemplos
    docs = [
        "O campo TIPMOV indica o tipo de movimentacao",
        "Pedidos de compra sao armazenados na tabela TGFCAB",
        "O estoque WMS fica na tabela TGWEST"
    ]
    embeddings.fit(docs)

    # Testar com texto em portugues
    texto = "Qual o tipo de movimentacao?"
    vetor = embeddings.embed_query(texto)

    print(f"Texto: {texto}")
    print(f"Dimensao do vetor: {len(vetor)}")
    print(f"Soma do vetor: {sum(vetor):.4f}")

    return True


if __name__ == "__main__":
    test_embeddings()
