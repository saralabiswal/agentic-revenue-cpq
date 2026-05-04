"""Compatibility exports for embedding providers used by RAG.

Author: Sarala Biswal
"""

from services.embeddings import (
    EmbeddingClient as EmbeddingClientProtocol,
    EmbeddingClientError,
    OllamaEmbeddingClient,
    ProviderEmbeddingClient,
    create_embedding_client,
)

# Backward-compatible local RAG import path. New code should depend on
# services.embeddings.EmbeddingClient for the provider-neutral interface.
EmbeddingClient = OllamaEmbeddingClient

__all__ = [
    "EmbeddingClient",
    "EmbeddingClientProtocol",
    "EmbeddingClientError",
    "OllamaEmbeddingClient",
    "ProviderEmbeddingClient",
    "create_embedding_client",
]
