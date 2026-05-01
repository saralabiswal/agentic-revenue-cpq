"""MCP tool wrappers that expose RAG retrieval to the agent.

Author: Sarala Biswal
"""

import logging
from collections.abc import Callable
from typing import Any

from services.mcp import ToolDefinition, ToolRegistry
from services.rag import Retriever


RetrieverFactory = Callable[[], Retriever]

logger = logging.getLogger(__name__)


def search_knowledge(
    query: str,
    k: int = 3,
    retriever: Retriever | None = None,
) -> dict[str, Any]:
    """Retrieve knowledge snippets for a natural-language query."""
    if not query:
        raise ValueError("query is required.")

    active_retriever = retriever or Retriever()
    logger.info("Searching knowledge base: query_length=%s k=%s", len(query), k)

    try:
        results = active_retriever.retrieve(query, k=k)
    except Exception:
        logger.exception("Knowledge search failed")
        results = []

    logger.info("Knowledge search completed: result_count=%s", len(results))
    return {
        "query": query,
        "results": results,
    }


def search_knowledge_tool(
    payload: dict[str, Any],
    retriever_factory: RetrieverFactory | None = None,
) -> dict[str, Any]:
    """MCP handler that validates and executes a knowledge search."""
    query = payload.get("query")
    if not isinstance(query, str) or not query:
        raise ValueError("query is required.")

    k = int(payload.get("k", 3))
    retriever = retriever_factory() if retriever_factory else None
    return search_knowledge(query=query, k=k, retriever=retriever)


def register_rag_tools(
    registry: ToolRegistry,
    retriever_factory: RetrieverFactory | None = None,
) -> ToolRegistry:
    """Register RAG search tools in the MCP registry."""

    def handler(payload: dict[str, Any]) -> dict[str, Any]:
        """Bind the optional retriever factory to the registered MCP handler."""
        return search_knowledge_tool(payload, retriever_factory=retriever_factory)

    registry.register(
        ToolDefinition(
            name="search_knowledge",
            handler=handler,
            description="Search the product, pricing, and sales playbook knowledge base.",
        )
    )
    return registry
