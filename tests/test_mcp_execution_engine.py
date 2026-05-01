"""Test coverage for mcp execution engine behavior.

Author: Sarala Biswal
"""

import logging

import pytest

from services.mcp import (
    MCPExecutionEngine,
    ToolDefinition,
    ToolExecutionError,
    ToolRegistry,
)


def test_execution_engine_runs_registered_tool_through_mcp(caplog: pytest.LogCaptureFixture) -> None:
    """Verify execution engine runs registered tool through mcp behavior."""
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="get_pricing",
            handler=lambda payload: {"total": payload["quantity"] * 25},
        )
    )
    engine = MCPExecutionEngine(registry)

    with caplog.at_level(logging.INFO):
        result = engine.execute("get_pricing", {"quantity": 4})

    assert result == {"total": 100}
    assert "Executing MCP tool: get_pricing" in caplog.text
    assert "payload_keys=['quantity']" in caplog.text
    assert "MCP tool completed: get_pricing" in caplog.text
    assert "result_keys=['total']" in caplog.text


def test_execution_engine_defaults_to_empty_payload() -> None:
    """Verify execution engine defaults to empty payload behavior."""
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="ping",
            handler=lambda payload: {"payload": payload},
        )
    )
    engine = MCPExecutionEngine(registry)

    assert engine.execute("ping") == {"payload": {}}


def test_execution_engine_rejects_non_dict_payload() -> None:
    """Verify execution engine rejects non dict payload behavior."""
    engine = MCPExecutionEngine(ToolRegistry())

    with pytest.raises(ToolExecutionError, match="payload must be a dictionary"):
        engine.execute("get_pricing", "invalid")  # type: ignore[arg-type]


def test_execution_engine_wraps_tool_errors(caplog: pytest.LogCaptureFixture) -> None:
    """Verify execution engine wraps tool errors behavior."""
    def failing_tool(_payload: dict) -> dict:
        """Verify failing tool behavior."""
        raise ValueError("bad integration response")

    registry = ToolRegistry()
    registry.register(ToolDefinition(name="create_quote", handler=failing_tool))
    engine = MCPExecutionEngine(registry)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ToolExecutionError, match="Tool execution failed"):
            engine.execute("create_quote", {"sf_opportunity_id": "SF-OPP-001"})

    assert "MCP tool failed: create_quote" in caplog.text


def test_execution_engine_rejects_non_dict_tool_result() -> None:
    """Verify execution engine rejects non dict tool result behavior."""
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="bad_tool",
            handler=lambda _payload: ["not", "a", "dict"],  # type: ignore[return-value]
        )
    )
    engine = MCPExecutionEngine(registry)

    with pytest.raises(ToolExecutionError, match="result must be a dictionary"):
        engine.execute("bad_tool", {})
