"""Integration tests for the official MCP stdio server.

Author: Sarala Biswal
"""

import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


EXPECTED_TOOLS = [
    "list_accounts",
    "list_opportunities",
    "get_opportunity",
    "list_quotes",
    "list_orders",
    "list_activity",
    "search_knowledge",
]


@pytest.mark.asyncio
async def test_mcp_stdio_server_discovers_and_executes_read_only_tools() -> None:
    """Verify stdio MCP discovery, success, validation, and hidden mutating tools."""
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "apps.mcp_server.main"],
        cwd=Path(__file__).resolve().parents[1],
        env=dict(os.environ, LLM_PROVIDER="fallback"),
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_response = await session.list_tools()
            assert [tool.name for tool in tools_response.tools] == EXPECTED_TOOLS

            accounts_response = await session.call_tool("list_accounts", {})
            assert accounts_response.isError is False
            assert "SF-ACC-" in accounts_response.content[0].text

            invalid_response = await session.call_tool("get_opportunity", {})
            assert invalid_response.isError is True
            assert "sf_opportunity_id" in invalid_response.content[0].text

            mutating_response = await session.call_tool(
                "create_quote",
                {"pricing": {"sf_opportunity_id": "SF-OPP-001"}},
            )
            assert mutating_response.isError is True
            assert "Unknown tool: create_quote" in mutating_response.content[0].text
