"""Package marker and exports for services.rag.

Author: Sarala Biswal
"""

from services.embeddings import (
    EmbeddingClient as EmbeddingClientProtocol,
    EmbeddingClientError,
    OllamaEmbeddingClient,
    create_embedding_client,
)
from services.rag.retriever import Retriever
from services.rag.vector_store import (
    ChromaVectorStore,
    ProviderVectorStore,
    VectorStore,
    VectorStoreError,
    create_vector_store,
)

# Public RAG API consumed by MCP tool wrappers and ingestion scripts.
__all__ = [
    "EmbeddingClient",
    "EmbeddingClientProtocol",
    "EmbeddingClientError",
    "OllamaEmbeddingClient",
    "Retriever",
    "ChromaVectorStore",
    "ProviderVectorStore",
    "VectorStore",
    "VectorStoreError",
    "create_embedding_client",
    "create_vector_store",
]

# Backward-compatible local RAG import path. New code should use
# services.embeddings.EmbeddingClient for the provider-neutral interface.
EmbeddingClient = OllamaEmbeddingClient
