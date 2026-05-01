"""Test coverage for cpq quote behavior.

Author: Sarala Biswal
"""

import pytest

from integrations.cpq import (
    QuoteCreationError,
    QuoteLifecycleError,
    create_quote,
    finalize_quote,
    get_pricing,
    list_orders,
    list_quotes,
    recommend_products,
)
from integrations.salesforce import get_opportunity


def test_create_quote_returns_draft_quote() -> None:
    """Verify create quote returns draft quote behavior."""
    pricing = get_pricing(recommend_products(get_opportunity("SF-OPP-001")))

    quote = create_quote(pricing)

    assert quote["oracle_quote_id"] == "ORA-Q-001-001"
    assert quote["sf_opportunity_id"] == "SF-OPP-001"
    assert quote["status"] == "DRAFT"
    assert quote["currency"] == "USD"
    assert quote["total"] == 1572500.0
    assert quote["selected_product_count"] == 7
    assert [item["sku"] for item in quote["line_items"]] == [
        "NTAP-AFF-A-SERIES",
        "NTAP-ASA-A-SERIES",
        "NTAP-STORAGEGRID",
        "NTAP-CVO",
        "NTAP-CONSOLE-OPS",
        "NTAP-PRO-SERVICES",
        "NTAP-PREMIUM-SUPPORT",
    ]


def test_create_quote_returns_copy_of_line_items() -> None:
    """Verify create quote returns copy of line items behavior."""
    pricing = get_pricing(recommend_products(get_opportunity("SF-OPP-001")))
    quote = create_quote(pricing)
    quote["line_items"][0]["name"] = "Changed"

    fresh_quote = create_quote(pricing)

    assert fresh_quote["line_items"][0]["name"] == "AFF A-Series Performance Storage"


def test_create_quote_can_persist_multiple_versions() -> None:
    """Verify create quote can persist multiple versions behavior."""
    pricing = get_pricing(recommend_products(get_opportunity("SF-OPP-001")))

    first_quote = create_quote(pricing, persist=True)
    second_quote = create_quote(pricing, persist=True)

    assert first_quote["oracle_quote_id"] == "ORA-Q-001-001"
    assert second_quote["oracle_quote_id"] == "ORA-Q-001-002"
    assert [quote["oracle_quote_id"] for quote in list_quotes("SF-OPP-001")] == [
        "ORA-Q-001-000",
        "ORA-Q-001-001",
        "ORA-Q-001-002",
    ]


def test_finalize_quote_places_order_and_supersedes_other_drafts() -> None:
    """Verify finalize quote places order and supersedes other drafts behavior."""
    pricing = get_pricing(recommend_products(get_opportunity("SF-OPP-001")))
    first_quote = create_quote(pricing, persist=True)
    second_quote = create_quote(pricing, persist=True)

    result = finalize_quote(second_quote["oracle_quote_id"])
    quotes = list_quotes("SF-OPP-001")

    assert result["quote"]["status"] == "ACCEPTED"
    assert result["order"]["oracle_order_id"] == "ORA-O-001-002"
    assert result["order"]["oracle_quote_id"] == second_quote["oracle_quote_id"]
    assert list_orders("SF-OPP-001")[0]["oracle_order_id"] == "ORA-O-001-002"
    assert next(
        quote for quote in quotes if quote["oracle_quote_id"] == first_quote["oracle_quote_id"]
    )["status"] == "SUPERSEDED"
    assert next(
        quote for quote in quotes if quote["oracle_quote_id"] == second_quote["oracle_quote_id"]
    )["status"] == "ACCEPTED"


def test_finalize_quote_rejects_superseded_quote() -> None:
    """Verify finalize quote rejects superseded quote behavior."""
    with pytest.raises(QuoteLifecycleError, match="Cannot finalize superseded quote"):
        finalize_quote("ORA-Q-001-000")


def test_create_quote_requires_opportunity_id() -> None:
    """Verify create quote requires opportunity id behavior."""
    with pytest.raises(QuoteCreationError, match="Salesforce opportunity id is required"):
        create_quote({"line_items": [{"sku": "NTAP-AFF-A-SERIES"}], "total": 75000.0})


def test_create_quote_requires_line_items() -> None:
    """Verify create quote requires line items behavior."""
    with pytest.raises(QuoteCreationError, match="Quote line items are required"):
        create_quote({"sf_opportunity_id": "SF-OPP-001", "line_items": [], "total": 75000.0})


def test_create_quote_requires_total() -> None:
    """Verify create quote requires total behavior."""
    with pytest.raises(QuoteCreationError, match="Quote total is required"):
        create_quote(
            {
                "sf_opportunity_id": "SF-OPP-001",
                "line_items": [{"sku": "NTAP-AFF-A-SERIES"}],
            }
        )
