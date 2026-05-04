"""Secrets provider boundary.

Author: Sarala Biswal
"""

from __future__ import annotations

import os
from typing import Protocol

from services.platform.config import PlatformConfig, get_platform_config


class SecretsProvider(Protocol):
    """Interface for reading runtime secrets."""

    def get_secret(self, name: str, default: str | None = None) -> str | None:
        """Return a secret value or the supplied default."""

    def require_secret(self, name: str) -> str:
        """Return a secret value or raise when it is absent."""


class EnvSecretsProvider:
    """Secrets provider backed by process environment variables."""

    def get_secret(self, name: str, default: str | None = None) -> str | None:
        """Read a secret from the environment."""
        return os.getenv(name, default)

    def require_secret(self, name: str) -> str:
        """Read a required secret from the environment."""
        value = self.get_secret(name)
        if value is None:
            raise KeyError(f"Required secret is not set: {name}")
        return value


class ProviderSecretsProvider:
    """Stub for cloud secret providers that are not implemented yet."""

    def __init__(self, provider_name: str) -> None:
        """Store provider name for clear runtime errors."""
        self._provider_name = provider_name

    def get_secret(self, name: str, default: str | None = None) -> str | None:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def require_secret(self, name: str) -> str:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def _not_implemented(self) -> NotImplementedError:
        """Build the clear stub error."""
        return NotImplementedError(
            f"SECRETS_PROVIDER={self._provider_name!r} is a stub. "
            "Use SECRETS_PROVIDER=env for local runs."
        )


def create_secrets_provider(config: PlatformConfig | None = None) -> SecretsProvider:
    """Create the configured secrets provider."""
    platform_config = config or get_platform_config()
    provider = platform_config.secrets_provider
    if provider == "env":
        return EnvSecretsProvider()
    if provider in {"oci_vault", "gcp_secret_manager"}:
        # Do not import cloud SDKs in the local profile. Real vault adapters can
        # be added later behind this SecretsProvider contract.
        return ProviderSecretsProvider(provider)

    raise ValueError(
        f"Unsupported SECRETS_PROVIDER={provider!r}. "
        "Supported values: env, oci_vault, gcp_secret_manager."
    )
