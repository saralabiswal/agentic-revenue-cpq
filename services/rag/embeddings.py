import logging
import os
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class EmbeddingClientError(RuntimeError):
    """Raised when Ollama returns an unusable embedding response."""


class EmbeddingClient:
    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.model = model
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._client = http_client or httpx.Client(timeout=timeout)

    def embed(self, texts: list[str]) -> list[list[float]]:
        logger.info("Generating embeddings: model=%s document_count=%s", self.model, len(texts))
        embeddings = [self._embed_one(text) for text in texts]
        logger.info("Generated embeddings: model=%s embedding_count=%s", self.model, len(embeddings))
        return embeddings

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "EmbeddingClient":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def _embed_one(self, text: str) -> list[float]:
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
            logger.error("Ollama embedding response missing embedding: model=%s", self.model)
            raise EmbeddingClientError("Ollama response did not include an embedding.")

        return [float(value) for value in embedding]
