"""Package marker and exports for services.mcp.

Author: Sarala Biswal
"""

from services.mcp.engine import MCPExecutionEngine, ToolExecutionError
from services.mcp.contracts import (
    MCP_TOOL_CONTRACTS,
    READ_ONLY_MCP_TOOL_NAMES,
    ToolContract,
    ToolContractError,
    get_tool_contract,
    validate_tool_payload,
)
from services.mcp.registry import (
    ToolDefinition,
    ToolHandler,
    ToolRegistry,
    ToolRegistryError,
)
from services.mcp.official_adapter import (
    CONFIRMATION_TOKEN_FIELD,
    MCPToolPolicy,
    OfficialMCPAdapterError,
    build_confirmation_token,
    execute_exposed_tool,
    list_exposed_tool_contracts,
)

# Public MCP API used by agent graph and tool registration modules.
__all__ = [
    "MCPExecutionEngine",
    "MCP_TOOL_CONTRACTS",
    "MCPToolPolicy",
    "CONFIRMATION_TOKEN_FIELD",
    "OfficialMCPAdapterError",
    "READ_ONLY_MCP_TOOL_NAMES",
    "ToolContract",
    "ToolContractError",
    "ToolDefinition",
    "ToolExecutionError",
    "ToolHandler",
    "ToolRegistry",
    "ToolRegistryError",
    "build_confirmation_token",
    "execute_exposed_tool",
    "get_tool_contract",
    "list_exposed_tool_contracts",
    "validate_tool_payload",
]
