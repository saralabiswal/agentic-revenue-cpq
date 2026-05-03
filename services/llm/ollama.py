"""Ollama-backed chat client implementation.

Author: Sarala Biswal
"""

import os
from typing import Any

import httpx

from services.llm.client import LLMClient, LLMMessage, LLMResponse

# Ollama client flow:
# - Agent graph builds OpenAI-style role/content messages.
# - This client posts those messages to Ollama's /api/chat endpoint.
# - It returns only the assistant message dictionary to satisfy LLMClient.


class OllamaClientError(RuntimeError):
    """Raised when Ollama returns an unusable response."""


class OllamaClient(LLMClient):
    """HTTP client for non-streaming Ollama chat completions."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Create an Ollama chat client for the configured model and endpoint."""
        # Environment overrides keep Docker/local model selection outside code.
        self.model = os.getenv("OLLAMA_MODEL", model)
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        # Tests inject a fake client; runtime uses httpx with a timeout.
        self._client = http_client or httpx.Client(timeout=timeout)

    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        """Send chat messages to Ollama and return the assistant message."""
        # stream=False keeps the service contract simple: one request, one response.
        response = self._client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
            },
        )
        response.raise_for_status()

        payload: dict[str, Any] = response.json()
        message = payload.get("message")
        if not isinstance(message, dict):
            # Fail loudly when Ollama responds but does not match the expected API shape.
            raise OllamaClientError("Ollama response did not include a message.")

        return message

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "OllamaClient":
        """Return this client for context-manager use."""
        return self

    def __exit__(self, *_exc_info: object) -> None:
        """Close the client when leaving a context-manager block."""
        self.close()
