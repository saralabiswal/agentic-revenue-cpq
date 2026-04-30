from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeAlias


ToolInput: TypeAlias = dict[str, Any]
ToolOutput: TypeAlias = dict[str, Any]
ToolHandler: TypeAlias = Callable[[ToolInput], ToolOutput]


class ToolRegistryError(ValueError):
    """Raised when a tool cannot be registered or fetched."""


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    handler: ToolHandler
    description: str = ""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if not tool.name:
            raise ToolRegistryError("Tool name is required.")

        if tool.name in self._tools:
            raise ToolRegistryError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolRegistryError(f"Tool not registered: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._tools)
