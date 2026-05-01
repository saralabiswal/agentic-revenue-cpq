"""Rule-based product recommendation logic for telecom opportunities.

Author: Sarala Biswal
"""

from typing import Any

from integrations.cpq.catalog import get_catalog_item


class ProductRecommendationError(ValueError):
    """Raised when recommendations cannot be produced for an opportunity."""


def recommend_products(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Build rule-based product recommendations for a Salesforce opportunity."""
    sf_opportunity_id = opportunity.get("sf_opportunity_id")
    if not sf_opportunity_id:
        raise ProductRecommendationError("Salesforce opportunity id is required.")

    term_months = int(opportunity.get("term_months", 12))
    amount = float(opportunity.get("amount", 0))
    requirements = opportunity.get("requirements", [])
    requirement_text = " ".join(str(requirement) for requirement in requirements).lower()

    products: list[dict[str, Any]] = []

    if _contains_any(requirement_text, ("low latency", "5g edge", "edge", "mission-critical")):
        products.append(
            _product(
                "NTAP-AFF-A-SERIES",
                quantity=2 if amount >= 1000000 else 1,
                term_months=term_months,
                reason="Matched low-latency and 5G edge storage requirements.",
                rule_id="RULE-EDGE-PERFORMANCE",
            )
        )

    if _contains_any(
        requirement_text,
        ("billing", "subscriber", "database", "vmware", "block", "san"),
    ):
        products.append(
            _product(
                "NTAP-ASA-A-SERIES",
                quantity=1,
                term_months=term_months,
                reason="Matched billing, subscriber, database, or block-storage workload requirements.",
                rule_id="RULE-BLOCK-CORE",
            )
        )

    if _contains_any(
        requirement_text,
        ("telemetry", "logs", "cdr", "archive", "data lake", "object"),
    ):
        products.append(
            _product(
                "NTAP-STORAGEGRID",
                quantity=2 if amount >= 600000 else 1,
                term_months=term_months,
                reason="Matched telemetry, CDR, archive, object-storage, and data-lake requirements.",
                rule_id="RULE-OBJECT-DATA-LAKE",
            )
        )

    if _contains_any(requirement_text, ("hybrid cloud", "disaster recovery", "dr", "cloud")):
        products.append(
            _product(
                "NTAP-CVO",
                quantity=1,
                term_months=term_months,
                reason="Matched hybrid cloud and disaster recovery requirements.",
                rule_id="RULE-HYBRID-DR",
            )
        )

    infrastructure_count = len(products)
    if infrastructure_count == 0:
        products.append(
            _product(
                "NTAP-AFF-A-SERIES",
                quantity=1,
                term_months=term_months,
                reason="Default performance storage recommendation for telecom infrastructure opportunities.",
                rule_id="RULE-DEFAULT-PERFORMANCE",
            )
        )
        infrastructure_count = 1

    if infrastructure_count >= 3 or _contains_any(requirement_text, ("centralized management", "operations")):
        products.append(
            _product(
                "NTAP-CONSOLE-OPS",
                quantity=1,
                term_months=term_months,
                reason="Recommended for centralized management across edge, core, and cloud storage.",
                rule_id="RULE-CENTRAL-MANAGEMENT",
            )
        )

    if infrastructure_count >= 2:
        products.append(
            _product(
                "NTAP-PRO-SERVICES",
                quantity=1,
                term_months=term_months,
                reason="Recommended to support deployment, migration planning, and operational handoff.",
                rule_id="RULE-DEPLOYMENT-SERVICES",
            )
        )

    if amount >= 1000000 or _contains_any(requirement_text, ("premium support", "mission-critical")):
        products.append(
            _product(
                "NTAP-PREMIUM-SUPPORT",
                quantity=1,
                term_months=term_months,
                reason="Recommended for mission-critical telecom operations and enterprise-scale support.",
                rule_id="RULE-PREMIUM-SUPPORT",
            )
        )

    return {
        "sf_opportunity_id": sf_opportunity_id,
        "currency": opportunity.get("currency", "USD"),
        "products": products,
    }


def _product(
    sku: str,
    quantity: int,
    term_months: int,
    reason: str,
    rule_id: str,
) -> dict[str, Any]:
    """Create one normalized product recommendation entry."""
    catalog_item = get_catalog_item(sku)
    if catalog_item is None:
        raise ProductRecommendationError(f"Unknown product SKU: {sku}")

    return {
        "sku": catalog_item.sku,
        "name": catalog_item.name,
        "category": catalog_item.category,
        "quantity": quantity,
        "term_months": term_months,
        "selected": True,
        "required": False,
        "billing_model": catalog_item.billing_model,
        "reason": reason,
        "rule_id": rule_id,
    }


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    """Return whether text contains any keyword in a case-insensitive comparison."""
    return any(keyword in text for keyword in keywords)
