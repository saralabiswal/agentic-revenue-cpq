"""In-process registry for MCP tool definitions and handlers.

Author: Sarala Biswal
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeAlias


ToolInput: TypeAlias = dict[str, Any]
ToolOutput: TypeAlias = dict[str, Any]
ToolHandler: TypeAlias = Callable[[ToolInput], ToolOutput]

# Registry contract:
# - A tool name is the public capability the agent can request.
# - A handler is regular Python code hidden behind that capability name.
# - The registry is intentionally small and in-process for this demo.


class ToolRegistryError(ValueError):
    """Raised when a tool cannot be registered or fetched."""


@dataclass(frozen=True)
class ToolDefinition:
    """Immutable description of a callable MCP tool."""

    name: str
    handler: ToolHandler
    description: str = ""


class ToolRegistry:
    """Registry that stores MCP tools by name and exposes lookup helpers."""

    def __init__(self) -> None:
        """Create an empty registry for tool definitions."""
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a named tool and reject empty or duplicate names."""
        if not tool.name:
            # Empty tool names would make logs and agent calls impossible to audit.
            raise ToolRegistryError("Tool name is required.")

        if tool.name in self._tools:
            # Duplicate names are rejected so one capability maps to one handler.
            raise ToolRegistryError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        """Return a registered tool definition by name."""
        try:
            return self._tools[name]
        except KeyError as exc:
            # Unknown capability requests should fail at the boundary.
            raise ToolRegistryError(f"Tool not registered: {name}") from exc

    def names(self) -> list[str]:
        """Return registered tool names in stable sorted order."""
        return sorted(self._tools)
