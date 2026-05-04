"""Business persistence provider boundary.

Author: Sarala Biswal
"""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any, Protocol

from services.platform import PlatformConfig, get_platform_config


logger = logging.getLogger(__name__)


class _SQLiteRepositoryProxy:
    """Lazy proxy that avoids business/data package import cycles."""

    def __getattr__(self, name: str) -> Any:
        """Load the SQLite repository module only when a method is called."""
        return getattr(import_module("services.data.repositories"), name)


sqlite_repositories = _SQLiteRepositoryProxy()

# Business store guardrail: cross-system identifiers remain source-prefixed in
# this boundary and API payloads: sf_* for Salesforce, oracle_* for Oracle CPQ.

class BusinessStore(Protocol):
    """Interface for account, opportunity, quote, order, activity, and run persistence."""

    def reset_business_data(self) -> None:
        """Reset seeded business data."""

    def list_accounts(self) -> list[dict[str, Any]]:
        """Return Salesforce account records."""

    def list_opportunities(self, sf_account_id: str | None = None) -> list[dict[str, Any]]:
        """Return Salesforce opportunity records."""

    def get_opportunity(self, sf_opportunity_id: str) -> dict[str, Any] | None:
        """Return one Salesforce opportunity."""

    def list_quotes(self, sf_opportunity_id: str) -> list[dict[str, Any]]:
        """Return Oracle quote versions for an opportunity."""

    def create_quote_record(self, pricing: dict[str, Any]) -> dict[str, Any]:
        """Persist an Oracle quote."""

    def finalize_quote_record(self, oracle_quote_id: str) -> dict[str, Any] | None:
        """Accept a quote and create or return the matching order."""

    def list_orders(self, sf_opportunity_id: str | None = None) -> list[dict[str, Any]]:
        """Return placed Oracle orders."""

    def get_order(self, oracle_order_id: str) -> dict[str, Any] | None:
        """Return one placed Oracle order."""

    def list_activity(
        self,
        sf_opportunity_id: str | None = None,
        sf_account_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return business activity events."""

    def record_activity(
        self,
        *,
        sf_opportunity_id: str | None = None,
        sf_account_id: str | None = None,
        system: str,
        event_type: str,
        title: str,
        detail: str,
        oracle_quote_id: str | None = None,
        oracle_order_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist one business activity event."""

    def record_agent_run(
        self,
        *,
        intent: str,
        status: str,
        steps: list[dict[str, Any]],
        sf_opportunity_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist one agent run and its steps."""

    def list_agent_runs(
        self,
        sf_opportunity_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return recent agent run summaries."""

    def get_agent_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one agent run with steps."""


class SQLiteBusinessStore:
    """BusinessStore implementation backed by the existing SQLite repositories."""

    def reset_business_data(self) -> None:
        """Reset seeded business data."""
        sqlite_repositories.reset_business_data()

    def list_accounts(self) -> list[dict[str, Any]]:
        """Return Salesforce account records."""
        return sqlite_repositories.list_accounts()

    def list_opportunities(self, sf_account_id: str | None = None) -> list[dict[str, Any]]:
        """Return Salesforce opportunity records."""
        return sqlite_repositories.list_opportunities(sf_account_id)

    def get_opportunity(self, sf_opportunity_id: str) -> dict[str, Any] | None:
        """Return one Salesforce opportunity."""
        return sqlite_repositories.get_opportunity(sf_opportunity_id)

    def list_quotes(self, sf_opportunity_id: str) -> list[dict[str, Any]]:
        """Return Oracle quote versions for an opportunity."""
        return sqlite_repositories.list_quotes(sf_opportunity_id)

    def create_quote_record(self, pricing: dict[str, Any]) -> dict[str, Any]:
        """Persist an Oracle quote."""
        return sqlite_repositories.create_quote_record(pricing)

    def finalize_quote_record(self, oracle_quote_id: str) -> dict[str, Any] | None:
        """Accept a quote and create or return the matching order."""
        return sqlite_repositories.finalize_quote_record(oracle_quote_id)

    def list_orders(self, sf_opportunity_id: str | None = None) -> list[dict[str, Any]]:
        """Return placed Oracle orders."""
        return sqlite_repositories.list_orders(sf_opportunity_id)

    def get_order(self, oracle_order_id: str) -> dict[str, Any] | None:
        """Return one placed Oracle order."""
        return sqlite_repositories.get_order(oracle_order_id)

    def list_activity(
        self,
        sf_opportunity_id: str | None = None,
        sf_account_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return business activity events."""
        return sqlite_repositories.list_activity(
            sf_opportunity_id=sf_opportunity_id,
            sf_account_id=sf_account_id,
        )

    def record_activity(
        self,
        *,
        sf_opportunity_id: str | None = None,
        sf_account_id: str | None = None,
        system: str,
        event_type: str,
        title: str,
        detail: str,
        oracle_quote_id: str | None = None,
        oracle_order_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist one business activity event."""
        return sqlite_repositories.record_activity(
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
        self,
        *,
        intent: str,
        status: str,
        steps: list[dict[str, Any]],
        sf_opportunity_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist one agent run and its steps."""
        return sqlite_repositories.record_agent_run(
            intent=intent,
            status=status,
            steps=steps,
            sf_opportunity_id=sf_opportunity_id,
        )

    def list_agent_runs(
        self,
        sf_opportunity_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return recent agent run summaries."""
        return sqlite_repositories.list_agent_runs(
            sf_opportunity_id=sf_opportunity_id,
            limit=limit,
        )

    def get_agent_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one agent run with steps."""
        return sqlite_repositories.get_agent_run(run_id)


class ProviderBusinessStore:
    """Stub for cloud business stores that are not implemented yet."""

    def __init__(self, provider_name: str) -> None:
        """Store provider name for clear runtime errors."""
        self._provider_name = provider_name

    def reset_business_data(self) -> None:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def list_accounts(self) -> list[dict[str, Any]]:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def list_opportunities(self, sf_account_id: str | None = None) -> list[dict[str, Any]]:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def get_opportunity(self, sf_opportunity_id: str) -> dict[str, Any] | None:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def list_quotes(self, sf_opportunity_id: str) -> list[dict[str, Any]]:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def create_quote_record(self, pricing: dict[str, Any]) -> dict[str, Any]:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def finalize_quote_record(self, oracle_quote_id: str) -> dict[str, Any] | None:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def list_orders(self, sf_opportunity_id: str | None = None) -> list[dict[str, Any]]:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def get_order(self, oracle_order_id: str) -> dict[str, Any] | None:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def list_activity(
        self,
        sf_opportunity_id: str | None = None,
        sf_account_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def record_activity(
        self,
        *,
        sf_opportunity_id: str | None = None,
        sf_account_id: str | None = None,
        system: str,
        event_type: str,
        title: str,
        detail: str,
        oracle_quote_id: str | None = None,
        oracle_order_id: str | None = None,
    ) -> dict[str, Any]:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def record_agent_run(
        self,
        *,
        intent: str,
        status: str,
        steps: list[dict[str, Any]],
        sf_opportunity_id: str | None = None,
    ) -> dict[str, Any]:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def list_agent_runs(
        self,
        sf_opportunity_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def get_agent_run(self, run_id: str) -> dict[str, Any] | None:
        """Raise until the provider integration is intentionally implemented."""
        raise self._not_implemented()

    def _not_implemented(self) -> NotImplementedError:
        """Build the clear stub error."""
        return NotImplementedError(
            f"BUSINESS_STORE_PROVIDER={self._provider_name!r} is a stub. "
            "Use BUSINESS_STORE_PROVIDER=sqlite for local runs."
        )


def create_business_store(config: PlatformConfig | None = None) -> BusinessStore:
    """Create the configured business store."""
    platform_config = config or get_platform_config()
    provider = platform_config.business_store_provider
    logger.info(
        "Business store provider selected: profile=%s provider=%s",
        platform_config.platform_profile,
        provider,
    )

    if provider == "sqlite":
        return SQLiteBusinessStore()
    if provider in {
        "oracle_autonomous_db",
        "cloud_sql_postgres",
        "alloydb",
        "postgres",
    }:
        # Cloud business stores are explicit stubs until adapter tasks add SDKs
        # or database drivers without changing repository call sites.
        return ProviderBusinessStore(provider)

    raise ValueError(
        f"Unsupported BUSINESS_STORE_PROVIDER={provider!r}. Supported values: sqlite, "
        "oracle_autonomous_db, cloud_sql_postgres, alloydb, postgres."
    )
