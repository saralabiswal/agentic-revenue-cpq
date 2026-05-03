"""Package marker and exports for services.llm.

Author: Sarala Biswal
"""

from services.llm.client import LLMClient, LLMMessage, LLMResponse
from services.llm.factory import create_llm_client
from services.llm.ollama import OllamaClient, OllamaClientError

# Public LLM API: graph code consumes the interface/factory and only concrete
# provider code imports Ollama directly.
__all__ = [
    "create_llm_client",
    "LLMClient",
    "LLMMessage",
    "LLMResponse",
    "OllamaClient",
    "OllamaClientError",
]
