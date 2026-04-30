from typing import Any

from services.data import (
    get_opportunity as repository_get_opportunity,
    list_accounts as repository_list_accounts,
    list_opportunities as repository_list_opportunities,
)


class OpportunityNotFoundError(LookupError):
    """Raised when a mock Salesforce opportunity is unavailable."""


def list_accounts() -> list[dict[str, Any]]:
    return repository_list_accounts()


def list_opportunities(sf_account_id: str | None = None) -> list[dict[str, Any]]:
    return repository_list_opportunities(sf_account_id)


def get_opportunity(sf_opportunity_id: str) -> dict[str, Any]:
    opportunity = repository_get_opportunity(sf_opportunity_id)
    if opportunity is None:
        raise OpportunityNotFoundError(f"Opportunity not found: {sf_opportunity_id}")

    return opportunity
