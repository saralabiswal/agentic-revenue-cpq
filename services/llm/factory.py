"""Factory for selecting the configured LLM provider.

Author: Sarala Biswal
"""

import logging
import os

from services.llm.client import LLMClient
from services.llm.ollama import OllamaClient


logger = logging.getLogger(__name__)


def create_llm_client() -> LLMClient | None:
    """Return the configured LLM client, or None for deterministic fallback mode."""
    provider = os.getenv("LLM_PROVIDER", "fallback").lower()
    if provider == "ollama":
        logger.info("LLM provider enabled: ollama")
        return OllamaClient()

    logger.info("LLM provider disabled: fallback_response")
    return None
