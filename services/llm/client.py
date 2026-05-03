"""Provider-neutral chat model interface used by agent workflows.

Author: Sarala Biswal
"""

from abc import ABC, abstractmethod
from typing import Any, TypeAlias


LLMMessage: TypeAlias = dict[str, Any]
LLMResponse: TypeAlias = dict[str, Any]

# LLM abstraction:
# - Agent graph code depends on this interface, not a specific provider SDK.
# - Returning dictionaries keeps fallback mode and Ollama mode compatible.


class LLMClient(ABC):
    """Provider-neutral interface for chat-style LLM calls."""

    @abstractmethod
    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        """Send chat messages and return one assistant-style response dictionary."""
        raise NotImplementedError
