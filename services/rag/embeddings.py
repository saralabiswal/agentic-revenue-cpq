"""Ollama embedding client used for local RAG ingestion and search.

Author: Sarala Biswal
"""

import logging
import os
from typing import Any

import httpx


logger = logging.getLogger(__name__)

# Embedding flow:
# - The caller passes plain text strings.
# - Each string is sent to Ollama's /api/embeddings endpoint.
# - Returned numeric vectors are passed to VectorStore for semantic search.


class EmbeddingClientError(RuntimeError):
    """Raised when Ollama returns an unusable embedding response."""


class EmbeddingClient:
    """HTTP client for generating embeddings with Ollama."""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Create an embedding client for the configured Ollama endpoint."""
        self.model = model
        # OLLAMA_BASE_URL lets Docker/local runs point to different Ollama hosts.
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        # Tests can inject a mock httpx.Client; runtime code uses a real client.
        self._client = http_client or httpx.Client(timeout=timeout)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate one embedding vector for each supplied text."""
        logger.info("Generating embeddings: model=%s document_count=%s", self.model, len(texts))
        # Ollama embeddings endpoint handles one prompt at a time in this client.
        embeddings = [self._embed_one(text) for text in texts]
        logger.info("Generated embeddings: model=%s embedding_count=%s", self.model, len(embeddings))
        return embeddings

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "EmbeddingClient":
        """Return this client for context-manager use."""
        return self

    def __exit__(self, *_exc_info: object) -> None:
        """Close the client when leaving a context-manager block."""
        self.close()

    def _embed_one(self, text: str) -> list[float]:
        """Request and validate one embedding vector from Ollama."""
        response = self._client.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text,
            },
        )
        response.raise_for_status()

        payload: dict[str, Any] = response.json()
        embedding = payload.get("embedding")
        if not isinstance(embedding, list):
            # Fail clearly if Ollama is reachable but returns an unexpected shape.
            logger.error("Ollama embedding response missing embedding: model=%s", self.model)
            raise EmbeddingClientError("Ollama response did not include an embedding.")

        # Normalize numeric types because JSON may return ints or floats.
        return [float(value) for value in embedding]
