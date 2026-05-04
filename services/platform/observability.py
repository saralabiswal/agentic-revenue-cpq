"""Observability provider boundary.

Author: Sarala Biswal
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from services.platform.config import PlatformConfig, get_platform_config


class ObservabilityProvider(Protocol):
    """Interface for logs and lightweight structured events."""

    def get_logger(self, name: str) -> logging.Logger:
        """Return a logger for a component name."""

    def record_event(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        level: int = logging.INFO,
    ) -> None:
        """Record a lightweight structured event."""


class PythonLoggingObservabilityProvider:
    """Observability provider backed by Python standard logging."""

    def get_logger(self, name: str) -> logging.Logger:
        """Return a standard Python logger."""
        return logging.getLogger(name)

    def record_event(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        level: int = logging.INFO,
    ) -> None:
        """Record an event through Python logging."""
        logging.getLogger("services.platform.observability").log(
            level,
            "Platform event: %s attributes=%s",
            name,
            attributes or {},
        )


class ProviderObservabilityProvider:
    """Stub for cloud observability providers that are not implemented yet."""

    def __init__(self, provider_name: str) -> None:
        """Store provider name for clear runtime errors."""
        self._provider_name = provider_name

    def get_logger(self, name: str) -> logging.Logger:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def record_event(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        level: int = logging.INFO,
    ) -> None:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def _not_implemented(self) -> NotImplementedError:
        """Build the clear stub error."""
        return NotImplementedError(
            f"OBSERVABILITY_PROVIDER={self._provider_name!r} is a stub. "
            "Use OBSERVABILITY_PROVIDER=python_logging for local runs."
        )


def create_observability_provider(
    config: PlatformConfig | None = None,
) -> ObservabilityProvider:
    """Create the configured observability provider."""
    platform_config = config or get_platform_config()
    provider = platform_config.observability_provider
    if provider == "python_logging":
        return PythonLoggingObservabilityProvider()
    if provider in {"oci_logging", "gcp_logging", "opentelemetry"}:
        return ProviderObservabilityProvider(provider)

    raise ValueError(
        f"Unsupported OBSERVABILITY_PROVIDER={provider!r}. "
        "Supported values: python_logging, oci_logging, gcp_logging, opentelemetry."
    )
