"""Test coverage for cloud-agnostic platform configuration.

Author: Sarala Biswal
"""

import pytest

from services.platform import get_platform_config


PROVIDER_ENV_VARS = [
    "PLATFORM_PROFILE",
    "AGENT_ORCHESTRATOR",
    "LLM_PROVIDER",
    "EMBEDDING_PROVIDER",
    "VECTOR_STORE_PROVIDER",
    "BUSINESS_STORE_PROVIDER",
    "OBJECT_STORE_PROVIDER",
    "SECRETS_PROVIDER",
    "OBSERVABILITY_PROVIDER",
]


def test_platform_profile_local_preserves_current_defaults(monkeypatch) -> None:
    """Verify local profile defaults remain credential-free and Ollama-backed."""
    for env_name in PROVIDER_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)

    config = get_platform_config()

    assert config.platform_profile == "local"
    assert config.agent_orchestrator == "langgraph"
    assert config.llm_provider == "ollama"
    assert config.embedding_provider == "ollama"
    assert config.vector_store_provider == "chroma"
    assert config.business_store_provider == "sqlite"
    assert config.object_store_provider == "local_fs"
    assert config.secrets_provider == "env"
    assert config.observability_provider == "python_logging"


def test_platform_profile_oci_selects_provider_defaults(monkeypatch) -> None:
    """Verify OCI profile selects provider names without importing OCI SDKs."""
    monkeypatch.setenv("PLATFORM_PROFILE", "oci")

    config = get_platform_config()

    assert config.platform_profile == "oci"
    assert config.agent_orchestrator == "native"
    assert config.llm_provider == "oci_genai"
    assert config.vector_store_provider == "oracle_23ai"
    assert config.business_store_provider == "oracle_autonomous_db"
    assert config.object_store_provider == "oci_object_storage"
    assert config.secrets_provider == "oci_vault"


def test_provider_environment_variables_override_profile_defaults(monkeypatch) -> None:
    """Verify explicit provider settings override profile defaults."""
    monkeypatch.setenv("PLATFORM_PROFILE", "gcp")
    monkeypatch.setenv("AGENT_ORCHESTRATOR", "langgraph")
    monkeypatch.setenv("LLM_PROVIDER", "fallback")

    config = get_platform_config()

    assert config.platform_profile == "gcp"
    assert config.agent_orchestrator == "langgraph"
    assert config.llm_provider == "fallback"
    assert config.embedding_provider == "vertex_ai"


def test_unknown_platform_profile_fails_clearly(monkeypatch) -> None:
    """Verify unsupported platform profiles fail before provider code runs."""
    monkeypatch.setenv("PLATFORM_PROFILE", "unknown-cloud")

    with pytest.raises(ValueError, match="Unsupported PLATFORM_PROFILE"):
        get_platform_config()
