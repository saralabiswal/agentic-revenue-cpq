import pytest

from services.mcp import ToolDefinition, ToolRegistry, ToolRegistryError


def quote_tool(payload: dict) -> dict:
    return {"oracle_quote_id": payload["oracle_quote_id"]}


def test_registry_registers_and_fetches_tool() -> None:
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="create_quote",
        handler=quote_tool,
        description="Create a CPQ quote.",
    )

    registry.register(tool)

    assert registry.get("create_quote") == tool
    assert registry.names() == ["create_quote"]


def test_registry_rejects_duplicate_tool_names() -> None:
    registry = ToolRegistry()
    tool = ToolDefinition(name="create_quote", handler=quote_tool)

    registry.register(tool)

    with pytest.raises(ToolRegistryError, match="already registered"):
        registry.register(tool)


def test_registry_rejects_empty_tool_name() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolRegistryError, match="name is required"):
        registry.register(ToolDefinition(name="", handler=quote_tool))


def test_registry_raises_for_unknown_tool() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolRegistryError, match="not registered"):
        registry.get("missing_tool")
