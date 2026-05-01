"""Provider-neutral chat model interface used by agent workflows.

Author: Sarala Biswal
"""

from abc import ABC, abstractmethod
from typing import Any, TypeAlias


LLMMessage: TypeAlias = dict[str, Any]
LLMResponse: TypeAlias = dict[str, Any]


class LLMClient(ABC):
    """Provider-neutral interface for chat-style LLM calls."""

    @abstractmethod
    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        """Run the full chat-driven opportunity-to-quote workflow."""
        raise NotImplementedError
