import pytest

from integrations.cpq import PricingError, get_pricing, recommend_products
from integrations.salesforce import get_opportunity


def test_get_pricing_returns_line_items_and_total() -> None:
    recommendation = recommend_products(get_opportunity("SF-OPP-001"))

    pricing = get_pricing(recommendation)

    assert pricing["sf_opportunity_id"] == "SF-OPP-001"
    assert pricing["currency"] == "USD"
    assert pricing["subtotal"] == 1850000.0
    assert pricing["discount"] == 277500.0
    assert pricing["discount_percent"] == 15.0
    assert pricing["total"] == 1572500.0
    assert [item["sku"] for item in pricing["line_items"]] == [
        "NTAP-AFF-A-SERIES",
        "NTAP-ASA-A-SERIES",
        "NTAP-STORAGEGRID",
        "NTAP-CVO",
        "NTAP-CONSOLE-OPS",
        "NTAP-PRO-SERVICES",
        "NTAP-PREMIUM-SUPPORT",
    ]


def test_get_pricing_scales_by_quantity_and_term() -> None:
    pricing = get_pricing(
        {
            "sf_opportunity_id": "SF-OPP-002",
            "currency": "USD",
            "products": [
                {
                    "sku": "NTAP-AFF-A-SERIES",
                    "name": "AFF A-Series Performance Storage",
                    "quantity": 2,
                    "term_months": 24,
                }
            ],
        }
    )

    assert pricing["line_items"][0]["net_price"] == 440000.0
    assert pricing["total"] == 440000.0


def test_get_pricing_requires_products() -> None:
    with pytest.raises(PricingError, match="Recommended products are required"):
        get_pricing({"sf_opportunity_id": "SF-OPP-002", "products": []})


def test_get_pricing_rejects_unknown_sku() -> None:
    with pytest.raises(PricingError, match="Unknown product SKU"):
        get_pricing(
            {
                "sf_opportunity_id": "SF-OPP-002",
                "products": [{"sku": "UNKNOWN", "quantity": 1, "term_months": 12}],
            }
        )
