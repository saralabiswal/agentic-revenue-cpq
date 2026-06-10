"""Test coverage for the official MCP server entrypoint wrappers.

Author: Sarala Biswal
"""

from typing import Any

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from apps.mcp_server import main as mcp_main


def test_mcp_server_read_only_tool_wrappers_delegate_with_payloads(monkeypatch) -> None:
    """Verify server wrapper functions delegate through the official adapter."""
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_execute(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        calls.append((tool_name, payload))
        return {"tool": tool_name, "payload": payload}

    monkeypatch.setattr(mcp_main, "execute_exposed_tool", fake_execute)

    assert mcp_main.list_accounts()["tool"] == "list_accounts"
    assert mcp_main.list_opportunities("SF-ACC-001")["payload"] == {
        "sf_account_id": "SF-ACC-001"
    }
    assert mcp_main.get_opportunity("SF-OPP-001")["tool"] == "get_opportunity"
    assert mcp_main.list_quotes("SF-OPP-001")["tool"] == "list_quotes"
    assert mcp_main.list_orders("SF-OPP-001")["tool"] == "list_orders"
    assert mcp_main.list_activity(sf_opportunity_id="SF-OPP-001")["payload"] == {
        "sf_opportunity_id": "SF-OPP-001"
    }
    assert mcp_main.search_knowledge("pricing", k=2)["payload"] == {
        "query": "pricing",
        "k": 2,
    }

    assert [tool_name for tool_name, _payload in calls] == [
        "list_accounts",
        "list_opportunities",
        "get_opportunity",
        "list_quotes",
        "list_orders",
        "list_activity",
        "search_knowledge",
    ]


@pytest.mark.asyncio
async def test_mcp_server_sdk_discovers_read_only_tools() -> None:
    """Verify the installed MCP SDK discovers the approved read-only tools."""
    server = mcp_main.create_mcp_server()

    tools = await server.list_tools()

    assert [tool.name for tool in tools] == [
        "list_accounts",
        "list_opportunities",
        "get_opportunity",
        "list_quotes",
        "list_orders",
        "list_activity",
        "search_knowledge",
    ]


@pytest.mark.asyncio
async def test_mcp_server_sdk_calls_read_only_tool() -> None:
    """Verify SDK tool invocation delegates to the internal MCP engine."""
    server = mcp_main.create_mcp_server()

    _content, structured = await server.call_tool("list_accounts", {})

    assert "accounts" in structured
    assert structured["accounts"][0]["sf_account_id"].startswith("SF-ACC-")


@pytest.mark.asyncio
async def test_mcp_server_sdk_rejects_invalid_tool_payload() -> None:
    """Verify SDK-level validation rejects invalid read-only tool payloads."""
    server = mcp_main.create_mcp_server()

    with pytest.raises(ToolError, match="sf_opportunity_id"):
        await server.call_tool("get_opportunity", {})


@pytest.mark.asyncio
async def test_mcp_server_sdk_exposes_rag_search_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify SDK-level RAG tool exposure preserves the existing result shape."""

    def fake_execute(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        assert tool_name == "search_knowledge"
        assert payload == {"query": "pricing rules", "k": 2}
        return {"query": payload["query"], "results": ["Pricing rules context"]}

    monkeypatch.setattr(mcp_main, "execute_exposed_tool", fake_execute)
    server = mcp_main.create_mcp_server()

    _content, structured = await server.call_tool(
        "search_knowledge",
        {"query": "pricing rules", "k": 2},
    )

    assert structured == {
        "query": "pricing rules",
        "results": ["Pricing rules context"],
    }
