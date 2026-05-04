"""Factory for selecting the configured LLM provider.

Author: Sarala Biswal
"""

import logging

from services.llm.client import LLMClient
from services.llm.ollama import OllamaClient
from services.platform import get_platform_config


logger = logging.getLogger(__name__)

# Provider selection flow:
# - Local default mode returns a live OllamaClient for natural-language responses.
# - LLM_PROVIDER=fallback returns None, so graph.py uses deterministic responses.


def create_llm_client() -> LLMClient | None:
    """Return the configured LLM client, or None for deterministic fallback mode."""
    provider = get_platform_config().llm_provider
    if provider == "fallback":
        # None is intentional: response nodes know to use fallback message builders.
        logger.info("LLM provider disabled: fallback_response")
        return None
    if provider == "ollama":
        # Live reasoning path. Prompt construction still stays in the agent graph.
        logger.info("LLM provider enabled: ollama")
        return OllamaClient()

    if provider in {"oci_genai", "vertex_ai"}:
        raise NotImplementedError(
            f"LLM_PROVIDER={provider!r} is a stub. "
            "Use LLM_PROVIDER=fallback or LLM_PROVIDER=ollama for local runs."
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER={provider!r}. Supported values: fallback, ollama, "
        "oci_genai, vertex_ai."
    )
