"""Factory for assembling the default MCP execution engine.

Author: Sarala Biswal
"""

from services.mcp.engine import MCPExecutionEngine
from services.tools import create_default_tool_registry


def create_default_mcp_engine() -> MCPExecutionEngine:
    """Create the default MCP execution engine with all standard tools registered."""
    return MCPExecutionEngine(create_default_tool_registry())
