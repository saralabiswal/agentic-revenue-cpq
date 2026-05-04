"""Test coverage for platform provider interfaces.

Author: Sarala Biswal
"""

import logging

import pytest

from services.platform import (
    EnvSecretsProvider,
    LocalFilesystemObjectStore,
    ProviderObjectStore,
    ProviderObservabilityProvider,
    ProviderSecretsProvider,
    PythonLoggingObservabilityProvider,
    create_object_store,
    create_observability_provider,
    create_secrets_provider,
)
from services.platform.config import PlatformConfig


def test_env_secrets_provider_reads_environment(monkeypatch) -> None:
    """Verify local secrets provider reads environment variables."""
    monkeypatch.setenv("DEMO_SECRET", "secret-value")

    provider = EnvSecretsProvider()

    assert provider.get_secret("DEMO_SECRET") == "secret-value"
    assert provider.get_secret("MISSING_SECRET", "fallback") == "fallback"
    assert provider.require_secret("DEMO_SECRET") == "secret-value"


def test_env_secrets_provider_requires_present_secret() -> None:
    """Verify missing required secrets fail clearly."""
    provider = EnvSecretsProvider()

    with pytest.raises(KeyError, match="Required secret"):
        provider.require_secret("MISSING_SECRET")


def test_local_filesystem_object_store_round_trip(tmp_path) -> None:
    """Verify local object store writes and reads bytes under its root."""
    store = LocalFilesystemObjectStore(root_path=tmp_path / "objects")

    key = store.put_object("runs/run-001.json", b'{"status":"ok"}')

    assert key == "runs/run-001.json"
    assert store.exists(key)
    assert store.get_object(key) == b'{"status":"ok"}'
    store.delete_object(key)
    assert not store.exists(key)


def test_local_filesystem_object_store_rejects_unsafe_keys(tmp_path) -> None:
    """Verify local object keys cannot escape the object store root."""
    store = LocalFilesystemObjectStore(root_path=tmp_path / "objects")

    with pytest.raises(ValueError, match="relative path"):
        store.put_object("../escape.txt", b"bad")


def test_python_logging_observability_provider_records_event(caplog) -> None:
    """Verify local observability provider uses Python logging."""
    provider = PythonLoggingObservabilityProvider()

    with caplog.at_level(logging.INFO):
        provider.record_event("demo.event", {"status": "ok"})

    assert provider.get_logger("demo.logger").name == "demo.logger"
    assert "Platform event: demo.event" in caplog.text
    assert "'status': 'ok'" in caplog.text


def test_platform_provider_factories_select_local_defaults(monkeypatch, tmp_path) -> None:
    """Verify local profile provider factories require no cloud credentials."""
    monkeypatch.setenv("PLATFORM_PROFILE", "local")
    monkeypatch.delenv("SECRETS_PROVIDER", raising=False)
    monkeypatch.delenv("OBJECT_STORE_PROVIDER", raising=False)
    monkeypatch.delenv("OBSERVABILITY_PROVIDER", raising=False)
    monkeypatch.setenv("OBJECT_STORE_PATH", str(tmp_path / "objects"))

    assert isinstance(create_secrets_provider(), EnvSecretsProvider)
    assert isinstance(create_object_store(), LocalFilesystemObjectStore)
    assert isinstance(create_observability_provider(), PythonLoggingObservabilityProvider)


def test_platform_provider_factories_return_oci_stubs() -> None:
    """Verify OCI platform providers are explicit stubs."""
    config = _platform_config(
        object_store_provider="oci_object_storage",
        secrets_provider="oci_vault",
        observability_provider="oci_logging",
    )

    secrets = create_secrets_provider(config)
    objects = create_object_store(config)
    observability = create_observability_provider(config)

    assert isinstance(secrets, ProviderSecretsProvider)
    assert isinstance(objects, ProviderObjectStore)
    assert isinstance(observability, ProviderObservabilityProvider)
    with pytest.raises(NotImplementedError, match="SECRETS_PROVIDER"):
        secrets.get_secret("demo")
    with pytest.raises(NotImplementedError, match="OBJECT_STORE_PROVIDER"):
        objects.get_object("demo.txt")
    with pytest.raises(NotImplementedError, match="OBSERVABILITY_PROVIDER"):
        observability.record_event("demo")


def test_platform_provider_factories_return_gcp_stubs() -> None:
    """Verify GCP platform providers are explicit stubs."""
    config = _platform_config(
        object_store_provider="gcs",
        secrets_provider="gcp_secret_manager",
        observability_provider="gcp_logging",
    )

    assert isinstance(create_secrets_provider(config), ProviderSecretsProvider)
    assert isinstance(create_object_store(config), ProviderObjectStore)
    assert isinstance(create_observability_provider(config), ProviderObservabilityProvider)


def _platform_config(
    object_store_provider: str = "local_fs",
    secrets_provider: str = "env",
    observability_provider: str = "python_logging",
) -> PlatformConfig:
    """Build provider config for platform provider tests."""
    return PlatformConfig(
        platform_profile="local",
        agent_orchestrator="langgraph",
        llm_provider="fallback",
        embedding_provider="ollama",
        vector_store_provider="chroma",
        business_store_provider="sqlite",
        object_store_provider=object_store_provider,
        secrets_provider=secrets_provider,
        observability_provider=observability_provider,
    )
