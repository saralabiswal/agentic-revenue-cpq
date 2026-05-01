"""Mock Oracle CPQ pricing engine for recommended product selections.

Author: Sarala Biswal
"""

from typing import Any

from integrations.cpq.catalog import get_catalog_item


class PricingError(ValueError):
    """Raised when pricing cannot be calculated for recommended products."""


def get_pricing(recommendation: dict[str, Any]) -> dict[str, Any]:
    """Calculate subtotal, discounts, and total for a recommendation payload."""
    products = [
        product
        for product in recommendation.get("products", [])
        if product.get("selected", True)
    ]
    if not isinstance(products, list) or not products:
        raise PricingError("Recommended products are required.")

    line_items = [_price_product(product) for product in products]
    subtotal = round(sum(item["net_price"] for item in line_items), 2)
    discounts = _calculate_discounts(line_items, recommendation)
    discount = round(sum(discount_item["amount"] for discount_item in discounts), 2)
    total = round(subtotal - discount, 2)
    discount_percent = round((discount / subtotal) * 100, 2) if subtotal else 0.0

    return {
        "sf_opportunity_id": recommendation.get("sf_opportunity_id"),
        "currency": recommendation.get("currency", "USD"),
        "line_items": line_items,
        "subtotal": subtotal,
        "discount": discount,
        "discount_percent": discount_percent,
        "discounts": discounts,
        "total": total,
    }


def _price_product(product: dict[str, Any]) -> dict[str, Any]:
    """Convert one recommended product into a priced CPQ line item."""
    sku = product.get("sku")
    catalog_item = get_catalog_item(str(sku))
    if catalog_item is None:
        raise PricingError(f"Unknown product SKU: {sku}")

    quantity = int(product.get("quantity", 1))
    term_months = int(product.get("term_months", 12))
    if quantity < 1:
        raise PricingError("Product quantity must be at least 1.")
    if term_months < 1:
        raise PricingError("Product term must be at least 1 month.")

    annual_unit_price = catalog_item.annual_unit_price
    if catalog_item.billing_model == "one_time":
        net_price = round(annual_unit_price * quantity, 2)
    else:
        net_price = round(annual_unit_price * quantity * (term_months / 12), 2)

    return {
        "sku": sku,
        "name": product.get("name", catalog_item.name),
        "category": catalog_item.category,
        "quantity": quantity,
        "term_months": term_months,
        "billing_model": catalog_item.billing_model,
        "annual_unit_price": annual_unit_price,
        "net_price": net_price,
    }


def _calculate_discounts(
    line_items: list[dict[str, Any]],
    recommendation: dict[str, Any],
) -> list[dict[str, Any]]:
    """Calculate all applicable quote discounts from opportunity and line-item context."""
    subtotal = round(sum(item["net_price"] for item in line_items), 2)
    term_months = max(int(item.get("term_months", 12)) for item in line_items)
    discounts: list[dict[str, Any]] = []

    if term_months >= 36:
        discounts.append(
            {
                "code": "TERM-36",
                "label": "36-month telecom modernization commitment",
                "percent": 10.0,
                "amount": round(subtotal * 0.10, 2),
            }
        )

    infrastructure_count = sum(
        1
        for item in line_items
        if item.get("category")
        in {"performance_storage", "block_storage", "object_storage", "hybrid_cloud"}
    )
    if infrastructure_count >= 3:
        discounts.append(
            {
                "code": "TELCO-BUNDLE",
                "label": "Multi-platform telecom bundle",
                "percent": 5.0,
                "amount": round(subtotal * 0.05, 2),
            }
        )

    if float(recommendation.get("manual_discount", 0.0)) > 0:
        manual_discount = float(recommendation["manual_discount"])
        discounts.append(
            {
                "code": "MANUAL",
                "label": "Sales-approved manual discount",
                "percent": 0.0,
                "amount": round(manual_discount, 2),
            }
        )

    return discounts
