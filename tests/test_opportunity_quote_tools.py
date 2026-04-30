import pytest

from services.mcp import MCPExecutionEngine, ToolExecutionError
from services.tools import create_default_tool_registry


def test_default_tool_registry_registers_opportunity_quote_tools() -> None:
    registry = create_default_tool_registry()

    assert registry.names() == [
        "create_quote",
        "finalize_quote",
        "get_opportunity",
        "get_pricing",
        "list_accounts",
        "list_activity",
        "list_opportunities",
        "list_orders",
        "list_quotes",
        "recommend_products",
        "search_knowledge",
    ]


def test_opportunity_quote_flow_executes_through_mcp_engine() -> None:
    engine = MCPExecutionEngine(create_default_tool_registry())

    opportunity = engine.execute("get_opportunity", {"sf_opportunity_id": "SF-OPP-001"})
    recommendation = engine.execute("recommend_products", {"opportunity": opportunity})
    pricing = engine.execute("get_pricing", {"recommendation": recommendation})
    quote = engine.execute("create_quote", {"pricing": pricing})

    assert opportunity["sf_opportunity_id"] == "SF-OPP-001"
    assert [product["sku"] for product in recommendation["products"]] == [
        "NTAP-AFF-A-SERIES",
        "NTAP-ASA-A-SERIES",
        "NTAP-STORAGEGRID",
        "NTAP-CVO",
        "NTAP-CONSOLE-OPS",
        "NTAP-PRO-SERVICES",
        "NTAP-PREMIUM-SUPPORT",
    ]
    assert pricing["total"] == 1572500.0
    assert quote["oracle_quote_id"] == "ORA-Q-001-001"
    assert quote["status"] == "DRAFT"


def test_account_opportunity_quote_and_order_lifecycle_tools() -> None:
    engine = MCPExecutionEngine(create_default_tool_registry())

    accounts = engine.execute("list_accounts", {})
    opportunities = engine.execute("list_opportunities", {"sf_account_id": "SF-ACC-001"})
    opportunity = engine.execute("get_opportunity", {"sf_opportunity_id": "SF-OPP-001"})
    recommendation = engine.execute("recommend_products", {"opportunity": opportunity})
    pricing = engine.execute("get_pricing", {"recommendation": recommendation})
    quote = engine.execute("create_quote", {"pricing": pricing, "persist": True})
    quote_history = engine.execute("list_quotes", {"sf_opportunity_id": "SF-OPP-001"})
    finalized = engine.execute(
        "finalize_quote",
        {"oracle_quote_id": quote["oracle_quote_id"]},
    )

    assert accounts["accounts"][0]["name"] == "Northstar Telecom"
    assert [item["sf_opportunity_id"] for item in opportunities["opportunities"]] == [
        "SF-OPP-002",
        "SF-OPP-001",
        "SF-OPP-003",
    ]
    assert quote["oracle_quote_id"] == "ORA-Q-001-001"
    assert quote_history["quotes"][-1]["oracle_quote_id"] == quote["oracle_quote_id"]
    assert finalized["quote"]["status"] == "ACCEPTED"
    assert finalized["order"]["status"] == "PLACED"


def test_get_opportunity_tool_requires_opportunity_id() -> None:
    engine = MCPExecutionEngine(create_default_tool_registry())

    with pytest.raises(ToolExecutionError, match="Tool execution failed"):
        engine.execute("get_opportunity", {})


def test_recommend_products_tool_requires_opportunity_dict() -> None:
    engine = MCPExecutionEngine(create_default_tool_registry())

    with pytest.raises(ToolExecutionError, match="Tool execution failed"):
        engine.execute("recommend_products", {"opportunity": "invalid"})


def test_get_pricing_tool_requires_recommendation_dict() -> None:
    engine = MCPExecutionEngine(create_default_tool_registry())

    with pytest.raises(ToolExecutionError, match="Tool execution failed"):
        engine.execute("get_pricing", {"recommendation": "invalid"})


def test_create_quote_tool_requires_pricing_dict() -> None:
    engine = MCPExecutionEngine(create_default_tool_registry())

    with pytest.raises(ToolExecutionError, match="Tool execution failed"):
        engine.execute("create_quote", {"pricing": "invalid"})
