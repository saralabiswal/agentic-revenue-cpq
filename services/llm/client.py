from abc import ABC, abstractmethod
from typing import Any, TypeAlias


LLMMessage: TypeAlias = dict[str, Any]
LLMResponse: TypeAlias = dict[str, Any]


class LLMClient(ABC):
    """Provider-neutral interface for chat-style LLM calls."""

    @abstractmethod
    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        raise NotImplementedError
