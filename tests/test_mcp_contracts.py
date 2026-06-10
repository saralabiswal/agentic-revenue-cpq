"""Test coverage for MCP exposure contracts.

Author: Sarala Biswal
"""

import pytest

from services.mcp import (
    MCP_TOOL_CONTRACTS,
    READ_ONLY_MCP_TOOL_NAMES,
    ToolContractError,
    validate_tool_payload,
)
from services.tools import create_default_tool_registry


def test_mcp_contracts_cover_registered_tools() -> None:
    """Verify every registered internal MCP tool has an exposure contract."""
    registry = create_default_tool_registry()

    assert set(MCP_TOOL_CONTRACTS) == set(registry.names())


def test_read_only_mcp_tool_names_are_initial_external_exposure_set() -> None:
    """Verify the first official MCP exposure set is read-only."""
    assert READ_ONLY_MCP_TOOL_NAMES == (
        "list_accounts",
        "list_opportunities",
        "get_opportunity",
        "list_quotes",
        "list_orders",
        "list_activity",
        "search_knowledge",
    )
    assert all(
        MCP_TOOL_CONTRACTS[tool_name].classification == "read_only"
        for tool_name in READ_ONLY_MCP_TOOL_NAMES
    )


def test_mcp_contracts_mark_mutating_tools_for_later_exposure() -> None:
    """Verify write-capable tools are not in the first external exposure set."""
    for tool_name in ["recommend_products", "create_quote", "finalize_quote"]:
        contract = MCP_TOOL_CONTRACTS[tool_name]

        assert contract.classification == "mutating"
        assert contract.exposure == "expose_later"


def test_validate_tool_payload_accepts_valid_read_payload() -> None:
    """Verify contract validation accepts known-good read payloads."""
    payload = validate_tool_payload(
        "get_opportunity",
        {"sf_opportunity_id": "SF-OPP-001"},
    )

    assert payload == {"sf_opportunity_id": "SF-OPP-001"}


def test_validate_tool_payload_rejects_missing_required_field() -> None:
    """Verify contract validation rejects missing required values."""
    with pytest.raises(ToolContractError, match="sf_opportunity_id is required"):
        validate_tool_payload("get_opportunity", {})


def test_validate_tool_payload_rejects_wrong_scalar_type() -> None:
    """Verify contract validation rejects scalar type mismatches."""
    with pytest.raises(ToolContractError, match="k must be an integer"):
        validate_tool_payload("search_knowledge", {"query": "pricing", "k": "3"})


def test_validate_tool_payload_rejects_wrong_object_type() -> None:
    """Verify contract validation rejects object type mismatches."""
    with pytest.raises(ToolContractError, match="pricing must be an object"):
        validate_tool_payload("create_quote", {"pricing": "not-an-object"})
