"""Factory for selecting the configured LLM provider.

Author: Sarala Biswal
"""

import logging
import os

from services.llm.client import LLMClient
from services.llm.ollama import OllamaClient


logger = logging.getLogger(__name__)

# Provider selection flow:
# - Default fallback mode returns None, so graph.py uses deterministic responses.
# - LLM_PROVIDER=ollama returns a live OllamaClient for natural-language responses.


def create_llm_client() -> LLMClient | None:
    """Return the configured LLM client, or None for deterministic fallback mode."""
    provider = os.getenv("LLM_PROVIDER", "fallback").lower()
    if provider == "ollama":
        # Live reasoning path. Prompt construction still stays in the agent graph.
        logger.info("LLM provider enabled: ollama")
        return OllamaClient()

    # None is intentional: response nodes know to use fallback message builders.
    logger.info("LLM provider disabled: fallback_response")
    return None
