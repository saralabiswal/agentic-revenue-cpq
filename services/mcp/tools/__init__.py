"""Package marker and exports for services.mcp.tools.

Author: Sarala Biswal
"""

from services.mcp.tools.rag_tools import (
    register_rag_tools,
    search_knowledge,
    search_knowledge_tool,
    warm_default_retriever,
)

# Expose tool-registration helpers that add specialized tools to the MCP registry.
__all__ = [
    "register_rag_tools",
    "search_knowledge",
    "search_knowledge_tool",
    "warm_default_retriever",
]
