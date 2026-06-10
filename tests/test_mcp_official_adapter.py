"""Test coverage for the official MCP adapter boundary.

Author: Sarala Biswal
"""

import pytest

from services.mcp import (
    CONFIRMATION_TOKEN_FIELD,
    MCPExecutionEngine,
    MCPToolPolicy,
    OfficialMCPAdapterError,
    ToolDefinition,
    ToolRegistry,
    build_confirmation_token,
    execute_exposed_tool,
    list_exposed_tool_contracts,
)


def test_list_exposed_tool_contracts_returns_read_only_contracts() -> None:
    """Verify official MCP discovery is limited to first-release read-only tools."""
    contracts = list_exposed_tool_contracts()

    assert [contract.name for contract in contracts] == [
        "list_accounts",
        "list_opportunities",
        "get_opportunity",
        "list_quotes",
        "list_orders",
        "list_activity",
        "search_knowledge",
    ]
    assert all(contract.exposure == "expose_now" for contract in contracts)
    assert all(contract.classification == "read_only" for contract in contracts)


def test_execute_exposed_tool_delegates_to_internal_engine() -> None:
    """Verify official MCP adapter delegates execution to MCPExecutionEngine."""
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="get_opportunity",
            handler=lambda payload: {"sf_opportunity_id": payload["sf_opportunity_id"]},
        )
    )

    result = execute_exposed_tool(
        "get_opportunity",
        {"sf_opportunity_id": "SF-OPP-001"},
        execution_engine=MCPExecutionEngine(registry),
    )

    assert result == {"sf_opportunity_id": "SF-OPP-001"}


def test_execute_exposed_tool_rejects_invalid_payload() -> None:
    """Verify official MCP adapter rejects payloads before engine execution."""
    with pytest.raises(OfficialMCPAdapterError, match="sf_opportunity_id is required"):
        execute_exposed_tool("get_opportunity", {})


def test_execute_exposed_tool_rejects_unknown_tool() -> None:
    """Verify official MCP adapter rejects tools without exposure contracts."""
    with pytest.raises(OfficialMCPAdapterError, match="contract not defined"):
        execute_exposed_tool("unknown_tool", {})


def test_execute_exposed_tool_denies_mutating_tool() -> None:
    """Verify official MCP adapter does not expose mutating tools by default."""
    with pytest.raises(OfficialMCPAdapterError, match="not externally exposed"):
        execute_exposed_tool(
            "create_quote",
            {"pricing": {"sf_opportunity_id": "SF-OPP-001"}},
        )


def test_execute_exposed_tool_allows_policy_approved_mutating_tool() -> None:
    """Verify policy-approved mutating tools still execute through the engine."""
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="create_quote",
            handler=lambda payload: {
                "oracle_quote_id": "ORA-Q-POLICY-001",
                "sf_opportunity_id": payload["pricing"]["sf_opportunity_id"],
            },
        )
    )

    result = execute_exposed_tool(
        "create_quote",
        {"pricing": {"sf_opportunity_id": "SF-OPP-001"}},
        execution_engine=MCPExecutionEngine(registry),
        policy=MCPToolPolicy(allowed_tool_names=frozenset({"create_quote"})),
    )

    assert result == {
        "oracle_quote_id": "ORA-Q-POLICY-001",
        "sf_opportunity_id": "SF-OPP-001",
    }


def test_execute_exposed_tool_requires_confirmation_for_persistent_quote() -> None:
    """Verify persistent quote creation needs confirmation even with policy approval."""
    with pytest.raises(OfficialMCPAdapterError, match="confirmation is required"):
        execute_exposed_tool(
            "create_quote",
            {"pricing": {"sf_opportunity_id": "SF-OPP-001"}, "persist": True},
            policy=MCPToolPolicy(allowed_tool_names=frozenset({"create_quote"})),
        )


def test_execute_exposed_tool_rejects_invalid_confirmation_token() -> None:
    """Verify confirmation tokens are tied to the exact tool payload."""
    with pytest.raises(OfficialMCPAdapterError, match="confirmation is required"):
        execute_exposed_tool(
            "create_quote",
            {
                "pricing": {"sf_opportunity_id": "SF-OPP-001"},
                "persist": True,
                CONFIRMATION_TOKEN_FIELD: "not-the-token",
            },
            policy=MCPToolPolicy(allowed_tool_names=frozenset({"create_quote"})),
        )


def test_execute_exposed_tool_accepts_confirmed_persistent_quote() -> None:
    """Verify confirmed persistent quote creation executes without leaking the token."""
    captured_payloads: list[dict] = []
    registry = ToolRegistry()

    def handler(payload: dict) -> dict:
        captured_payloads.append(payload)
        return {
            "oracle_quote_id": "ORA-Q-CONFIRMED-001",
            "sf_opportunity_id": payload["pricing"]["sf_opportunity_id"],
        }

    registry.register(ToolDefinition(name="create_quote", handler=handler))
    payload = {"pricing": {"sf_opportunity_id": "SF-OPP-001"}, "persist": True}
    payload[CONFIRMATION_TOKEN_FIELD] = build_confirmation_token("create_quote", payload)

    result = execute_exposed_tool(
        "create_quote",
        payload,
        execution_engine=MCPExecutionEngine(registry),
        policy=MCPToolPolicy(allowed_tool_names=frozenset({"create_quote"})),
    )

    assert result["oracle_quote_id"] == "ORA-Q-CONFIRMED-001"
    assert captured_payloads == [
        {"pricing": {"sf_opportunity_id": "SF-OPP-001"}, "persist": True}
    ]


def test_execute_exposed_tool_requires_confirmation_for_finalize_quote() -> None:
    """Verify quote finalization requires confirmation."""
    with pytest.raises(OfficialMCPAdapterError, match="confirmation is required"):
        execute_exposed_tool(
            "finalize_quote",
            {"oracle_quote_id": "ORA-Q-001-001"},
            policy=MCPToolPolicy(allowed_tool_names=frozenset({"finalize_quote"})),
        )


def test_execute_exposed_tool_accepts_confirmed_finalize_quote() -> None:
    """Verify confirmed quote finalization executes through the engine."""
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="finalize_quote",
            handler=lambda payload: {
                "quote": {"oracle_quote_id": payload["oracle_quote_id"]},
                "order": {"oracle_order_id": "ORA-O-CONFIRMED-001"},
            },
        )
    )
    payload = {"oracle_quote_id": "ORA-Q-001-001"}
    payload[CONFIRMATION_TOKEN_FIELD] = build_confirmation_token("finalize_quote", payload)

    result = execute_exposed_tool(
        "finalize_quote",
        payload,
        execution_engine=MCPExecutionEngine(registry),
        policy=MCPToolPolicy(allowed_tool_names=frozenset({"finalize_quote"})),
    )

    assert result == {
        "quote": {"oracle_quote_id": "ORA-Q-001-001"},
        "order": {"oracle_order_id": "ORA-O-CONFIRMED-001"},
    }
