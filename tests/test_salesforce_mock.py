import pytest

from integrations.salesforce import (
    OpportunityNotFoundError,
    get_opportunity,
    list_accounts,
    list_opportunities,
)


def test_list_accounts_returns_portfolio_accounts() -> None:
    accounts = list_accounts()

    assert len(accounts) >= 3
    assert accounts[0]["name"] == "Northstar Telecom"
    assert accounts[0]["opportunity_count"] >= 2
    assert accounts[0]["open_pipeline"] > 0


def test_list_opportunities_can_filter_by_account() -> None:
    opportunities = list_opportunities("SF-ACC-001")

    assert [opportunity["sf_opportunity_id"] for opportunity in opportunities] == [
        "SF-OPP-002",
        "SF-OPP-001",
        "SF-OPP-003",
    ]


def test_get_opportunity_returns_mock_opportunity() -> None:
    opportunity = get_opportunity("SF-OPP-001")

    assert opportunity["sf_opportunity_id"] == "SF-OPP-001"
    assert opportunity["account"]["name"] == "Northstar Telecom"
    assert opportunity["account"]["industry"] == "Telecommunications"
    assert opportunity["stage"] == "Proposal"
    assert opportunity["currency"] == "USD"
    assert "low latency storage for 5G edge applications" in opportunity["requirements"]


def test_get_opportunity_returns_copy() -> None:
    opportunity = get_opportunity("SF-OPP-001")
    opportunity["account"]["name"] = "Changed"

    fresh_opportunity = get_opportunity("SF-OPP-001")

    assert fresh_opportunity["account"]["name"] == "Northstar Telecom"


def test_get_opportunity_raises_for_unknown_opportunity() -> None:
    with pytest.raises(OpportunityNotFoundError, match="Opportunity not found"):
        get_opportunity("SF-OPP-404")
