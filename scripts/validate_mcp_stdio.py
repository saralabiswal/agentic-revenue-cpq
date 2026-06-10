"""Validate the official MCP stdio server with the Python MCP client.

Author: Sarala Biswal
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

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


async def validate() -> None:
    """Connect to the local stdio MCP server and validate core operations."""
    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.setdefault("LLM_PROVIDER", "fallback")

    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "apps.mcp_server.main"],
        cwd=project_root,
        env=env,
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            tool_names = [tool.name for tool in tools_response.tools]
            if tool_names != EXPECTED_TOOLS:
                raise AssertionError(f"Unexpected MCP tools: {tool_names}")

            accounts_response = await session.call_tool("list_accounts", {})
            if accounts_response.isError:
                raise AssertionError("list_accounts returned an MCP error")
            if "SF-ACC-" not in accounts_response.content[0].text:
                raise AssertionError("list_accounts response did not include account data")

            rag_response = await session.call_tool(
                "search_knowledge",
                {"query": "pricing rules", "k": 2},
            )
            if rag_response.isError:
                raise AssertionError("search_knowledge returned an MCP error")

            print("MCP stdio validation passed.")
            print(f"Discovered tools: {', '.join(tool_names)}")


if __name__ == "__main__":
    asyncio.run(validate())
