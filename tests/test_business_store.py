"""Test coverage for BusinessStore provider boundary.

Author: Sarala Biswal
"""

import pytest

from services.business import (
    ProviderBusinessStore,
    SQLiteBusinessStore,
    create_business_store,
)
from services.platform.config import PlatformConfig


def test_business_store_factory_selects_sqlite_for_local_profile(monkeypatch) -> None:
    """Verify local profile keeps the SQLite business store."""
    monkeypatch.setenv("PLATFORM_PROFILE", "local")
    monkeypatch.delenv("BUSINESS_STORE_PROVIDER", raising=False)

    store = create_business_store()

    assert isinstance(store, SQLiteBusinessStore)
    assert store.list_accounts()[0]["sf_account_id"] == "SF-ACC-001"


def test_sqlite_business_store_preserves_quote_lifecycle() -> None:
    """Verify SQLite business store wraps existing quote and order behavior."""
    store = SQLiteBusinessStore()
    opportunity = store.get_opportunity("SF-OPP-001")
    assert opportunity is not None
    pricing = {
        "sf_opportunity_id": opportunity["sf_opportunity_id"],
        "currency": "USD",
        "line_items": [
            {
                "sku": "NTAP-AFF-A-SERIES",
                "name": "AFF A-Series Performance Storage",
                "category": "performance_storage",
                "quantity": 1,
                "term_months": 12,
                "billing_model": "annual",
                "annual_unit_price": 100.0,
                "net_price": 100.0,
            }
        ],
        "subtotal": 100.0,
        "discount": 0.0,
        "discount_percent": 0.0,
        "total": 100.0,
    }

    quote = store.create_quote_record(pricing)
    finalized = store.finalize_quote_record(quote["oracle_quote_id"])

    assert quote["oracle_quote_id"] == "ORA-Q-001-001"
    assert finalized is not None
    assert finalized["quote"]["status"] == "ACCEPTED"
    assert finalized["order"]["oracle_quote_id"] == quote["oracle_quote_id"]


def test_business_store_factory_returns_cloud_provider_stub() -> None:
    """Verify cloud business stores are explicit stubs."""
    store = create_business_store(config=_platform_config("oracle_autonomous_db"))

    assert isinstance(store, ProviderBusinessStore)
    with pytest.raises(NotImplementedError, match="BUSINESS_STORE_PROVIDER"):
        store.list_accounts()


def _platform_config(business_store_provider: str) -> PlatformConfig:
    """Build provider config for business store factory tests."""
    return PlatformConfig(
        platform_profile="local",
        agent_orchestrator="langgraph",
        llm_provider="fallback",
        embedding_provider="ollama",
        vector_store_provider="chroma",
        business_store_provider=business_store_provider,
        object_store_provider="local_fs",
        secrets_provider="env",
        observability_provider="python_logging",
    )
