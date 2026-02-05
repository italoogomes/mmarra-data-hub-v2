# -*- coding: utf-8 -*-
"""
Vector Store Simples para RAG

Usa TF-IDF + Cosine Similarity para busca.
Funciona 100% offline, sem dependencias externas.
"""

import logging
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from langchain_core.documents import Document

from .embeddings import get_embeddings, TfidfEmbeddings

logger = logging.getLogger(__name__)

# Diretorio raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

# Diretorio para salvar o indice
INDEX_DIR = PROJECT_ROOT / "src" / "data" / "rag_index"

# Configuracoes de chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def simple_text_splitter(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Divide texto em chunks simples."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Tentar quebrar em fim de paragrafo ou frase
        if end < len(text):
            # Procurar quebra de paragrafo
            newline_pos = text.rfind('\n\n', start, end)
            if newline_pos > start + chunk_size // 2:
                end = newline_pos + 2
            else:
                # Procurar fim de frase
                period_pos = text.rfind('. ', start, end)
                if period_pos > start + chunk_size // 2:
                    end = period_pos + 2

        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if c]  # Remover vazios


class DocumentStore:
    """
    Gerencia documentos e busca por similaridade.

    Uso:
        store = DocumentStore()
        store.build_index()  # Primeira vez
        docs = store.search("como consultar estoque")
    """

    # Pastas e padroes de arquivos para indexar
    # ATUALIZADO v2.0 - Mais fontes de conhecimento
    DOCUMENT_SOURCES = [
        # === DOCUMENTAÇÃO PRINCIPAL ===
        {"path": "docs/de-para/sankhya", "glob": "*.md", "desc": "Mapeamento tabelas Sankhya"},
        {"path": "docs/de-para", "glob": "*.md", "desc": "Mapeamentos gerais"},
        {"path": "docs/investigacoes", "glob": "*.md", "desc": "Investigacoes realizadas"},
        {"path": "docs/bugs", "glob": "*.md", "desc": "Bugs conhecidos"},
        {"path": "docs/erros", "glob": "*.md", "desc": "Erros comuns e solucoes"},
        {"path": "docs/agentes", "glob": "*.md", "desc": "Specs dos agentes"},
        {"path": "docs/wms", "glob": "*.md", "desc": "Documentacao WMS"},
        {"path": "docs/api", "glob": "*.md", "desc": "Documentacao API Sankhya"},
        {"path": "docs/guias", "glob": "*.md", "desc": "Guias praticos"},
        {"path": "docs/modelos", "glob": "*.md", "desc": "Modelos ML"},
        {"path": "docs/data-lake", "glob": "*.md", "desc": "Estrutura Data Lake"},
        {"path": "docs/pipelines", "glob": "*.md", "desc": "Documentacao pipelines"},
        
        # === QUERIES SQL ===
        {"path": "queries", "glob": "**/*.sql", "desc": "Queries SQL funcionais"},
        {"path": "queries/compras", "glob": "*.sql", "desc": "Queries de compras"},
        {"path": "queries/vendas", "glob": "*.sql", "desc": "Queries de vendas"},
        {"path": "queries/estoque", "glob": "*.sql", "desc": "Queries de estoque"},
        
        # === ERROS E DIVERGENCIAS ===
        {"path": "output/divergencias", "glob": "*.txt", "desc": "Divergencias encontradas"},
        {"path": "output/divergencias", "glob": "*.md", "desc": "Analises de divergencias"},
        
        # === ARQUIVOS DE CONTEXTO (RAIZ) ===
        {"path": ".", "glob": "CLAUDE.md", "desc": "Instrucoes para IA"},
        {"path": ".", "glob": "PROGRESSO_ATUAL.md", "desc": "Estado atual do projeto"},
        
        # === POSTMAN (documentacao API) ===
        {"path": "postman", "glob": "*.md", "desc": "Documentacao Postman"},
    ]

    def __init__(self, index_path: Optional[Path] = None):
        """Inicializa o DocumentStore."""
        self.index_path = index_path or INDEX_DIR
        self.embeddings: TfidfEmbeddings = get_embeddings()
        self.documents: List[Document] = []
        self.vectors: Optional[np.ndarray] = None

    def _load_documents(self) -> List[Document]:
        """Carrega todos os documentos das fontes configuradas."""
        all_docs = []

        for source in self.DOCUMENT_SOURCES:
            source_path = PROJECT_ROOT / source["path"]

            if not source_path.exists():
                logger.debug(f"Pasta nao encontrada: {source_path}")
                continue

            glob_pattern = source["glob"]
            desc = source["desc"]

            logger.info(f"Carregando {desc} de {source_path}")

            try:
                # Buscar arquivos
                files = list(source_path.glob(glob_pattern.replace("**/", "")))

                # Buscar em subpastas se necessario
                if "**" in glob_pattern:
                    for subdir in source_path.iterdir():
                        if subdir.is_dir():
                            files.extend(subdir.glob(glob_pattern.split("/")[-1]))

                for file_path in files:
                    if file_path.is_file():
                        try:
                            content = file_path.read_text(encoding="utf-8")

                            # Dividir em chunks
                            chunks = simple_text_splitter(content)

                            for i, chunk in enumerate(chunks):
                                doc = Document(
                                    page_content=chunk,
                                    metadata={
                                        "source_type": desc,
                                        "file_name": file_path.name,
                                        "file_path": str(file_path.relative_to(PROJECT_ROOT)),
                                        "chunk_index": i
                                    }
                                )
                                all_docs.append(doc)

                            logger.debug(f"  {file_path.name}: {len(chunks)} chunks")

                        except Exception as e:
                            logger.warning(f"  Erro ao carregar {file_path}: {e}")

            except Exception as e:
                logger.error(f"Erro ao processar {source_path}: {e}")

        logger.info(f"Total de documentos/chunks carregados: {len(all_docs)}")
        return all_docs

    def build_index(self, force: bool = False) -> int:
        """
        Constroi o indice a partir dos documentos.

        Args:
            force: Se True, reconstroi mesmo se ja existir

        Returns:
            Numero de chunks indexados
        """
        # Verificar se ja existe
        if not force and (self.index_path / "index.pkl").exists():
            logger.info("Indice ja existe. Use force=True para reconstruir.")
            self.load_index()
            return len(self.documents)

        logger.info("Construindo indice RAG...")

        # Carregar documentos
        self.documents = self._load_documents()

        if not self.documents:
            logger.warning("Nenhum documento encontrado para indexar!")
            return 0

        # Criar embeddings
        logger.info(f"Criando embeddings para {len(self.documents)} chunks...")
        texts = [doc.page_content for doc in self.documents]

        # Treinar o vetorizador e obter vetores
        self.embeddings.fit(texts)
        self.vectors = np.array(self.embeddings.embed_documents(texts))

        # Salvar indice
        self.index_path.mkdir(parents=True, exist_ok=True)
        with open(self.index_path / "index.pkl", "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "vectors": self.vectors,
                "vectorizer": self.embeddings.vectorizer
            }, f)

        logger.info(f"Indice salvo em: {self.index_path}")
        return len(self.documents)

    def load_index(self) -> bool:
        """Carrega indice existente."""
        index_file = self.index_path / "index.pkl"

        if not index_file.exists():
            logger.warning(f"Indice nao encontrado em: {index_file}")
            return False

        logger.info(f"Carregando indice de: {index_file}")

        with open(index_file, "rb") as f:
            data = pickle.load(f)

        self.documents = data["documents"]
        self.vectors = data["vectors"]
        self.embeddings.vectorizer = data["vectorizer"]
        self.embeddings._fitted = True

        logger.info(f"Indice carregado: {len(self.documents)} documentos")
        return True

    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Busca documentos similares a query.

        Args:
            query: Texto de busca
            k: Numero de resultados

        Returns:
            Lista de documentos relevantes
        """
        if self.vectors is None or len(self.documents) == 0:
            if not self.load_index():
                logger.error("Indice nao disponivel. Execute build_index() primeiro.")
                return []

        # Obter embedding da query
        query_vector = np.array([self.embeddings.embed_query(query)])

        # Calcular similaridade
        similarities = cosine_similarity(query_vector, self.vectors)[0]

        # Ordenar por similaridade
        top_indices = np.argsort(similarities)[::-1][:k]

        # Retornar documentos com scores
        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            doc.metadata["relevance_score"] = float(similarities[idx])
            results.append(doc)

        return results

    def search_with_scores(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """Busca documentos com scores."""
        docs = self.search(query, k)
        return [(doc, doc.metadata.get("relevance_score", 0)) for doc in docs]

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatisticas do indice."""
        return {
            "status": "ativo" if self.vectors is not None else "nao_inicializado",
            "total_chunks": len(self.documents) if self.documents else 0,
            "index_path": str(self.index_path),
        }


def build_rag_index(force: bool = False) -> int:
    """Funcao de conveniencia para construir o indice."""
    store = DocumentStore()
    return store.build_index(force=force)


if __name__ == "__main__":
    # Teste rapido
    logging.basicConfig(level=logging.INFO)

    store = DocumentStore()
    n_chunks = store.build_index(force=True)
    print(f"\nIndice construido com {n_chunks} chunks")

    # Testar busca
    query = "O que significa o campo TIPMOV?"
    results = store.search(query, k=3)

    print(f"\nBusca: '{query}'")
    print(f"Resultados: {len(results)}")
    for i, doc in enumerate(results, 1):
        print(f"\n--- Resultado {i} (score: {doc.metadata.get('relevance_score', 0):.3f}) ---")
        print(f"Fonte: {doc.metadata.get('file_path', 'N/A')}")
        print(f"Conteudo: {doc.page_content[:200]}...")
