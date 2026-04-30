import logging
import os

from services.llm.client import LLMClient
from services.llm.ollama import OllamaClient


logger = logging.getLogger(__name__)


def create_llm_client() -> LLMClient | None:
    provider = os.getenv("LLM_PROVIDER", "fallback").lower()
    if provider == "ollama":
        logger.info("LLM provider enabled: ollama")
        return OllamaClient()

    logger.info("LLM provider disabled: fallback_response")
    return None
