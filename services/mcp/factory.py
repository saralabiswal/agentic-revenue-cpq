from services.mcp.engine import MCPExecutionEngine
from services.tools import create_default_tool_registry


def create_default_mcp_engine() -> MCPExecutionEngine:
    return MCPExecutionEngine(create_default_tool_registry())
