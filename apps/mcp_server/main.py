"""Official MCP server entrypoint for approved external tools.

Author: Sarala Biswal
"""

from __future__ import annotations

from typing import Any

from services.mcp import execute_exposed_tool


def _load_fastmcp_class() -> type:
    """Import FastMCP lazily so tests can run before the SDK is installed."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional package
        raise RuntimeError(
            "Official MCP SDK is not installed. Run `uv add \"mcp[cli]\"` first."
        ) from exc

    return FastMCP


def create_mcp_server() -> Any:
    """Create the official MCP server exposing approved read-only tools."""
    fastmcp_class = _load_fastmcp_class()
    server = fastmcp_class(
        "Enterprise AI Agent Platform",
        instructions="Read-only opportunity-to-quote tools backed by the internal MCP engine.",
    )

    server.add_tool(
        fn=list_accounts,
        name="list_accounts",
        description="List Salesforce-style accounts for the quote command center.",
    )
    server.add_tool(
        fn=list_opportunities,
        name="list_opportunities",
        description="List Salesforce-style opportunities, optionally filtered by account.",
    )
    server.add_tool(
        fn=get_opportunity,
        name="get_opportunity",
        description="Fetch one Salesforce-style opportunity by id.",
    )
    server.add_tool(
        fn=list_quotes,
        name="list_quotes",
        description="List CPQ-style quote versions for an opportunity.",
    )
    server.add_tool(
        fn=list_orders,
        name="list_orders",
        description="List placed orders, optionally filtered by opportunity.",
    )
    server.add_tool(
        fn=list_activity,
        name="list_activity",
        description="List business activity events for an account or opportunity.",
    )
    server.add_tool(
        fn=search_knowledge,
        name="search_knowledge",
        description="Search product, pricing, and sales playbook knowledge snippets.",
    )
    return server


def list_accounts() -> dict[str, Any]:
    """List Salesforce-style accounts."""
    return execute_exposed_tool("list_accounts", {})


def list_opportunities(sf_account_id: str | None = None) -> dict[str, Any]:
    """List Salesforce-style opportunities, optionally filtered by account."""
    payload = {"sf_account_id": sf_account_id} if sf_account_id else {}
    return execute_exposed_tool("list_opportunities", payload)


def get_opportunity(sf_opportunity_id: str) -> dict[str, Any]:
    """Fetch one Salesforce-style opportunity by id."""
    return execute_exposed_tool("get_opportunity", {"sf_opportunity_id": sf_opportunity_id})


def list_quotes(sf_opportunity_id: str) -> dict[str, Any]:
    """List quote versions for one opportunity."""
    return execute_exposed_tool("list_quotes", {"sf_opportunity_id": sf_opportunity_id})


def list_orders(sf_opportunity_id: str | None = None) -> dict[str, Any]:
    """List placed orders, optionally filtered by opportunity."""
    payload = {"sf_opportunity_id": sf_opportunity_id} if sf_opportunity_id else {}
    return execute_exposed_tool("list_orders", payload)


def list_activity(
    sf_opportunity_id: str | None = None,
    sf_account_id: str | None = None,
) -> dict[str, Any]:
    """List business activity events for an account or opportunity."""
    payload: dict[str, Any] = {}
    if sf_opportunity_id:
        payload["sf_opportunity_id"] = sf_opportunity_id
    if sf_account_id:
        payload["sf_account_id"] = sf_account_id
    return execute_exposed_tool("list_activity", payload)


def search_knowledge(query: str, k: int = 3) -> dict[str, Any]:
    """Search product, pricing, and sales playbook knowledge snippets."""
    return execute_exposed_tool("search_knowledge", {"query": query, "k": k})


def main() -> None:
    """Run the official MCP server over local stdio."""
    create_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
