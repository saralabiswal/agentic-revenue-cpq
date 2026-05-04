"""Embedding provider exports.

Author: Sarala Biswal
"""

from services.embeddings.client import EmbeddingClient
from services.embeddings.factory import ProviderEmbeddingClient, create_embedding_client
from services.embeddings.ollama import EmbeddingClientError, OllamaEmbeddingClient

__all__ = [
    "EmbeddingClient",
    "EmbeddingClientError",
    "OllamaEmbeddingClient",
    "ProviderEmbeddingClient",
    "create_embedding_client",
]
