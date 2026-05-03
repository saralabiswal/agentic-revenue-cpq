"""Package marker and exports for services.rag.

Author: Sarala Biswal
"""

from services.rag.embeddings import EmbeddingClient, EmbeddingClientError
from services.rag.retriever import Retriever
from services.rag.vector_store import VectorStore, VectorStoreError

# Public RAG API consumed by MCP tool wrappers and ingestion scripts.
__all__ = [
    "EmbeddingClient",
    "EmbeddingClientError",
    "Retriever",
    "VectorStore",
    "VectorStoreError",
]
