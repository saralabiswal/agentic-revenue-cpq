import pytest

from integrations.cpq import ProductRecommendationError, recommend_products
from integrations.salesforce import get_opportunity


def test_recommend_products_returns_base_products_for_opportunity() -> None:
    opportunity = get_opportunity("SF-OPP-001")

    recommendation = recommend_products(opportunity)

    assert recommendation["sf_opportunity_id"] == "SF-OPP-001"
    assert recommendation["currency"] == "USD"
    assert [product["sku"] for product in recommendation["products"]] == [
        "NTAP-AFF-A-SERIES",
        "NTAP-ASA-A-SERIES",
        "NTAP-STORAGEGRID",
        "NTAP-CVO",
        "NTAP-CONSOLE-OPS",
        "NTAP-PRO-SERVICES",
        "NTAP-PREMIUM-SUPPORT",
    ]
    assert all(product["selected"] for product in recommendation["products"])
    assert all(product["term_months"] == 36 for product in recommendation["products"])


def test_recommend_products_uses_defaults_for_optional_fields() -> None:
    recommendation = recommend_products({"sf_opportunity_id": "SF-OPP-002"})

    assert recommendation["currency"] == "USD"
    assert len(recommendation["products"]) == 1
    assert recommendation["products"][0]["sku"] == "NTAP-AFF-A-SERIES"
    assert recommendation["products"][0]["name"] == "AFF A-Series Performance Storage"
    assert recommendation["products"][0]["term_months"] == 12


def test_recommend_products_requires_opportunity_id() -> None:
    with pytest.raises(ProductRecommendationError, match="Salesforce opportunity id is required"):
        recommend_products({})
