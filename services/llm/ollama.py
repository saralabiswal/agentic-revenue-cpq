import os
from typing import Any

import httpx

from services.llm.client import LLMClient, LLMMessage, LLMResponse


class OllamaClientError(RuntimeError):
    """Raised when Ollama returns an unusable response."""


class OllamaClient(LLMClient):
    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.model = os.getenv("OLLAMA_MODEL", model)
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._client = http_client or httpx.Client(timeout=timeout)

    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
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
            raise OllamaClientError("Ollama response did not include a message.")

        return message

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "OllamaClient":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()
