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
_cached_default_retriever: Retriever | None = None

# RAG tool flow:
# - Agent calls MCP tool name `search_knowledge`.
# - This module validates payload and calls Retriever.
# - Retriever embeds the query and searches ChromaDB.
# - The result is returned as a dictionary for MCP/agent consistency.


def search_knowledge(
    query: str,
    k: int = 3,
    retriever: Retriever | None = None,
) -> dict[str, Any]:
    """Retrieve knowledge snippets for a natural-language query."""
    if not query:
        # Keep this validation here because it is the tool boundary for RAG search.
        raise ValueError("query is required.")

    logger.info("Searching knowledge base: query_length=%s k=%s", len(query), k)

    try:
        # Tests can inject a fake retriever; production/default code constructs one.
        # Keep construction inside the fallback guard because local ChromaDB or
        # embedding dependencies may be unavailable during deterministic app flows.
        active_retriever = retriever or _cached_default_retriever or Retriever()
        results = active_retriever.retrieve(query, k=k)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        # Knowledge retrieval should not take down the sales workflow; an empty
        # context result lets the agent continue with deterministic tool data.
        logger.exception("Knowledge search failed")
        results = []

    logger.info("Knowledge search completed: result_count=%s", len(results))
    return {
        "query": query,
        "results": results,
    }


def warm_default_retriever() -> bool:
    """Initialize the default retriever before request worker threads use it."""
    global _cached_default_retriever
    if _cached_default_retriever is not None:
        return True

    try:
        _cached_default_retriever = Retriever()
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        logger.exception("Knowledge retriever warmup failed")
        return False

    logger.info("Knowledge retriever warmup completed")
    return True


def search_knowledge_tool(
    payload: dict[str, Any],
    retriever_factory: RetrieverFactory | None = None,
) -> dict[str, Any]:
    """MCP handler that validates and executes a knowledge search."""
    query = payload.get("query")
    if not isinstance(query, str) or not query:
        raise ValueError("query is required.")

    # `k` controls how many snippets return to the agent prompt.
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
