from typing import Any

from integrations.cpq import (
    create_quote,
    finalize_quote,
    get_pricing,
    list_orders,
    list_quotes,
    recommend_products,
)
from integrations.salesforce import get_opportunity, list_accounts, list_opportunities
from services.data import list_activity, record_activity
from services.mcp import ToolDefinition, ToolRegistry
from services.mcp.tools import register_rag_tools


def list_accounts_tool(_payload: dict[str, Any]) -> dict[str, Any]:
    return {"accounts": list_accounts()}


def list_opportunities_tool(payload: dict[str, Any]) -> dict[str, Any]:
    sf_account_id = payload.get("sf_account_id")
    return {
        "opportunities": list_opportunities(
            str(sf_account_id) if sf_account_id else None
        )
    }


def get_opportunity_tool(payload: dict[str, Any]) -> dict[str, Any]:
    sf_opportunity_id = _required(payload, "sf_opportunity_id")
    return get_opportunity(str(sf_opportunity_id))


def recommend_products_tool(payload: dict[str, Any]) -> dict[str, Any]:
    opportunity = _required(payload, "opportunity")
    if not isinstance(opportunity, dict):
        raise ValueError("opportunity must be a dictionary.")

    recommendation = recommend_products(opportunity)
    record_activity(
        sf_opportunity_id=str(recommendation["sf_opportunity_id"]),
        system="Agentic Orchestration App",
        event_type="recommendation_generated",
        title="Agent generated product recommendation",
        detail=f"Recommended {len(recommendation['products'])} CPQ products.",
    )
    return recommendation


def get_pricing_tool(payload: dict[str, Any]) -> dict[str, Any]:
    recommendation = _required(payload, "recommendation")
    if not isinstance(recommendation, dict):
        raise ValueError("recommendation must be a dictionary.")

    return get_pricing(recommendation)


def create_quote_tool(payload: dict[str, Any]) -> dict[str, Any]:
    pricing = _required(payload, "pricing")
    if not isinstance(pricing, dict):
        raise ValueError("pricing must be a dictionary.")

    return create_quote(pricing, persist=bool(payload.get("persist", False)))


def list_quotes_tool(payload: dict[str, Any]) -> dict[str, Any]:
    sf_opportunity_id = _required(payload, "sf_opportunity_id")
    return {"quotes": list_quotes(str(sf_opportunity_id))}


def finalize_quote_tool(payload: dict[str, Any]) -> dict[str, Any]:
    oracle_quote_id = _required(payload, "oracle_quote_id")
    return finalize_quote(str(oracle_quote_id))


def list_orders_tool(payload: dict[str, Any]) -> dict[str, Any]:
    sf_opportunity_id = payload.get("sf_opportunity_id")
    return {"orders": list_orders(str(sf_opportunity_id) if sf_opportunity_id else None)}


def list_activity_tool(payload: dict[str, Any]) -> dict[str, Any]:
    sf_opportunity_id = payload.get("sf_opportunity_id")
    sf_account_id = payload.get("sf_account_id")
    return {
        "activity": list_activity(
            sf_opportunity_id=str(sf_opportunity_id) if sf_opportunity_id else None,
            sf_account_id=str(sf_account_id) if sf_account_id else None,
        )
    }


def register_opportunity_quote_tools(registry: ToolRegistry) -> ToolRegistry:
    registry.register(
        ToolDefinition(
            name="list_accounts",
            handler=list_accounts_tool,
            description="List Salesforce accounts for the quote command center.",
        )
    )
    registry.register(
        ToolDefinition(
            name="list_opportunities",
            handler=list_opportunities_tool,
            description="List Salesforce opportunities, optionally filtered by account.",
        )
    )
    registry.register(
        ToolDefinition(
            name="get_opportunity",
            handler=get_opportunity_tool,
            description="Fetch a Salesforce opportunity by id.",
        )
    )
    registry.register(
        ToolDefinition(
            name="recommend_products",
            handler=recommend_products_tool,
            description="Recommend CPQ products for an opportunity.",
        )
    )
    registry.register(
        ToolDefinition(
            name="get_pricing",
            handler=get_pricing_tool,
            description="Calculate quote pricing for recommended products.",
        )
    )
    registry.register(
        ToolDefinition(
            name="create_quote",
            handler=create_quote_tool,
            description="Create a draft CPQ quote from pricing.",
        )
    )
    registry.register(
        ToolDefinition(
            name="list_quotes",
            handler=list_quotes_tool,
            description="List CPQ quote versions for an opportunity.",
        )
    )
    registry.register(
        ToolDefinition(
            name="finalize_quote",
            handler=finalize_quote_tool,
            description="Accept a CPQ quote and place an order.",
        )
    )
    registry.register(
        ToolDefinition(
            name="list_orders",
            handler=list_orders_tool,
            description="List placed orders, optionally filtered by opportunity.",
        )
    )
    registry.register(
        ToolDefinition(
            name="list_activity",
            handler=list_activity_tool,
            description="List business activity events, optionally filtered by opportunity.",
        )
    )
    return registry


def create_default_tool_registry() -> ToolRegistry:
    registry = register_opportunity_quote_tools(ToolRegistry())
    return register_rag_tools(registry)


def _required(payload: dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"{key} is required.")

    return value
