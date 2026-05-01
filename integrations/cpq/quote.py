"""Mock Oracle CPQ quote and order lifecycle operations.

Author: Sarala Biswal
"""

from copy import deepcopy
import re
from typing import Any

from services.data import (
    create_quote_record,
    finalize_quote_record,
    list_orders as repository_list_orders,
    list_quotes as repository_list_quotes,
)


class QuoteCreationError(ValueError):
    """Raised when a mock CPQ quote cannot be created."""


class QuoteLifecycleError(ValueError):
    """Raised when a mock CPQ quote lifecycle action cannot be completed."""


def create_quote(pricing: dict[str, Any], persist: bool = False) -> dict[str, Any]:
    """Create a draft quote, optionally persisting it in the repository."""
    sf_opportunity_id = pricing.get("sf_opportunity_id")
    if not sf_opportunity_id:
        raise QuoteCreationError("Salesforce opportunity id is required.")

    line_items = pricing.get("line_items")
    if not isinstance(line_items, list) or not line_items:
        raise QuoteCreationError("Quote line items are required.")

    total = pricing.get("total")
    if total is None:
        raise QuoteCreationError("Quote total is required.")

    if persist:
        return create_quote_record(pricing)

    return {
        "oracle_quote_id": f"ORA-Q-{_record_number(str(sf_opportunity_id))}-001",
        "sf_opportunity_id": sf_opportunity_id,
        "status": "DRAFT",
        "currency": pricing.get("currency", "USD"),
        "line_items": deepcopy(line_items),
        "subtotal": pricing.get("subtotal", total),
        "discount": pricing.get("discount", 0.0),
        "discount_percent": pricing.get("discount_percent", 0.0),
        "selected_product_count": len(line_items),
        "total": total,
    }


def list_quotes(sf_opportunity_id: str) -> list[dict[str, Any]]:
    """Return all quote versions for a Salesforce opportunity."""
    return repository_list_quotes(sf_opportunity_id)


def finalize_quote(oracle_quote_id: str) -> dict[str, Any]:
    """Accept a quote and create or return the matching order."""
    try:
        result = finalize_quote_record(oracle_quote_id)
    except ValueError as exc:
        raise QuoteLifecycleError(str(exc)) from exc

    if result is None:
        raise QuoteLifecycleError(f"Quote not found: {oracle_quote_id}")

    return result


def list_orders(sf_opportunity_id: str | None = None) -> list[dict[str, Any]]:
    """Return placed orders, optionally filtered by Salesforce opportunity."""
    return repository_list_orders(sf_opportunity_id)


def reset_quote_lifecycle() -> None:
    """Reset seeded quote and order state for deterministic tests."""
    from services.data import reset_business_data

    reset_business_data()


def _record_number(source_id: str) -> str:
    """Derive the stable numeric portion used in Oracle quote identifiers."""
    match = re.search(r"(\d+)$", source_id)
    if match:
        return f"{int(match.group(1)):03d}"

    compacted = re.sub(r"[^A-Za-z0-9]+", "-", source_id).strip("-")
    return compacted[:12] or "000"
