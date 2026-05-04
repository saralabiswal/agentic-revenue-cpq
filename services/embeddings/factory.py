"""Embedding provider factory.

Author: Sarala Biswal
"""

import logging

from services.embeddings.client import EmbeddingClient
from services.embeddings.ollama import OllamaEmbeddingClient
from services.platform import PlatformConfig, get_platform_config


logger = logging.getLogger(__name__)


class ProviderEmbeddingClient:
    """Stub for cloud embedding providers that are not implemented yet."""

    def __init__(self, provider_name: str) -> None:
        """Store provider name for clear runtime errors."""
        self._provider_name = provider_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise NotImplementedError(
            f"EMBEDDING_PROVIDER={self._provider_name!r} is a stub. "
            "Use EMBEDDING_PROVIDER=ollama for local runs."
        )


def create_embedding_client(config: PlatformConfig | None = None) -> EmbeddingClient:
    """Create the configured embedding client."""
    platform_config = config or get_platform_config()
    provider = platform_config.embedding_provider
    logger.info(
        "Embedding provider selected: profile=%s provider=%s",
        platform_config.platform_profile,
        provider,
    )

    if provider == "ollama":
        return OllamaEmbeddingClient()
    if provider in {"oci_genai", "vertex_ai"}:
        # Cloud embedding providers are intentionally stubs here; adding real
        # SDK clients belongs inside provider adapters, not RAG call sites.
        return ProviderEmbeddingClient(provider)

    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER={provider!r}. "
        "Supported values: ollama, oci_genai, vertex_ai."
    )
