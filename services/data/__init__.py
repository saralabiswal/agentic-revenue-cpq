"""Package marker and exports for services.data.

Author: Sarala Biswal
"""

from services.data.database import get_database_path, initialize_database
from services.business import create_business_store

# Re-export business-store-backed functions as the public data-service API.
# Integrations and backend routes should import from here instead of reaching
# into database internals or provider-specific store implementations.


def reset_business_data() -> None:
    """Reset all seeded CRM, CPQ, activity, and agent run data."""
    create_business_store().reset_business_data()


def list_accounts() -> list[dict]:
    """Return Salesforce accounts from the configured business store."""
    return create_business_store().list_accounts()


def list_opportunities(sf_account_id: str | None = None) -> list[dict]:
    """Return Salesforce opportunities from the configured business store."""
    return create_business_store().list_opportunities(sf_account_id)


def get_opportunity(sf_opportunity_id: str) -> dict | None:
    """Return one Salesforce opportunity from the configured business store."""
    return create_business_store().get_opportunity(sf_opportunity_id)


def list_quotes(sf_opportunity_id: str) -> list[dict]:
    """Return Oracle quote versions from the configured business store."""
    return create_business_store().list_quotes(sf_opportunity_id)


def create_quote_record(pricing: dict) -> dict:
    """Persist one Oracle quote through the configured business store."""
    return create_business_store().create_quote_record(pricing)


def finalize_quote_record(oracle_quote_id: str) -> dict | None:
    """Finalize one Oracle quote through the configured business store."""
    return create_business_store().finalize_quote_record(oracle_quote_id)


def list_orders(sf_opportunity_id: str | None = None) -> list[dict]:
    """Return placed Oracle orders from the configured business store."""
    return create_business_store().list_orders(sf_opportunity_id)


def get_order(oracle_order_id: str) -> dict | None:
    """Return one Oracle order from the configured business store."""
    return create_business_store().get_order(oracle_order_id)


def list_activity(
    sf_opportunity_id: str | None = None,
    sf_account_id: str | None = None,
) -> list[dict]:
    """Return business activity events from the configured business store."""
    return create_business_store().list_activity(
        sf_opportunity_id=sf_opportunity_id,
        sf_account_id=sf_account_id,
    )


def record_activity(
    *,
    sf_opportunity_id: str | None = None,
    sf_account_id: str | None = None,
    system: str,
    event_type: str,
    title: str,
    detail: str,
    oracle_quote_id: str | None = None,
    oracle_order_id: str | None = None,
) -> dict:
    """Persist a business activity event through the configured business store."""
    return create_business_store().record_activity(
        sf_opportunity_id=sf_opportunity_id,
        sf_account_id=sf_account_id,
        system=system,
        event_type=event_type,
        title=title,
        detail=detail,
        oracle_quote_id=oracle_quote_id,
        oracle_order_id=oracle_order_id,
    )


def record_agent_run(
    *,
    intent: str,
    status: str,
    steps: list[dict],
    sf_opportunity_id: str | None = None,
) -> dict:
    """Persist an agent run through the configured business store."""
    return create_business_store().record_agent_run(
        intent=intent,
        status=status,
        steps=steps,
        sf_opportunity_id=sf_opportunity_id,
    )


def list_agent_runs(
    sf_opportunity_id: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Return recent agent run summaries from the configured business store."""
    return create_business_store().list_agent_runs(
        sf_opportunity_id=sf_opportunity_id,
        limit=limit,
    )


def get_agent_run(run_id: str) -> dict | None:
    """Return one agent run from the configured business store."""
    return create_business_store().get_agent_run(run_id)
__all__ = [
    "create_quote_record",
    "finalize_quote_record",
    "get_agent_run",
    "get_database_path",
    "get_order",
    "get_opportunity",
    "initialize_database",
    "list_agent_runs",
    "list_accounts",
    "list_activity",
    "list_opportunities",
    "list_orders",
    "list_quotes",
    "record_agent_run",
    "record_activity",
    "reset_business_data",
]
