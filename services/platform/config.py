"""Centralized cloud-agnostic provider configuration.

Author: Sarala Biswal
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


LOCAL_PROVIDER_DEFAULTS = {
    "agent_orchestrator": "langgraph",
    "llm_provider": "ollama",
    "embedding_provider": "ollama",
    "vector_store_provider": "chroma",
    "business_store_provider": "sqlite",
    "object_store_provider": "local_fs",
    "secrets_provider": "env",
    "observability_provider": "python_logging",
}

PROFILE_PROVIDER_DEFAULTS = {
    "local": LOCAL_PROVIDER_DEFAULTS,
    "oci": {
        "agent_orchestrator": "native",
        "llm_provider": "oci_genai",
        "embedding_provider": "oci_genai",
        "vector_store_provider": "oracle_23ai",
        "business_store_provider": "oracle_autonomous_db",
        "object_store_provider": "oci_object_storage",
        "secrets_provider": "oci_vault",
        "observability_provider": "oci_logging",
    },
    "gcp": {
        "agent_orchestrator": "native",
        "llm_provider": "vertex_ai",
        "embedding_provider": "vertex_ai",
        "vector_store_provider": "vertex_vector_search",
        "business_store_provider": "cloud_sql_postgres",
        "object_store_provider": "gcs",
        "secrets_provider": "gcp_secret_manager",
        "observability_provider": "gcp_logging",
    },
    "generic-kubernetes": {
        "agent_orchestrator": "native",
        "llm_provider": "fallback",
        "embedding_provider": "ollama",
        "vector_store_provider": "chroma",
        "business_store_provider": "sqlite",
        "object_store_provider": "local_fs",
        "secrets_provider": "env",
        "observability_provider": "python_logging",
    },
}

# UI-facing labels only. These mappings intentionally avoid URLs, credentials,
# and connection strings so /runtime/profile can be safe to expose read-only.
PROFILE_DISPLAY_SUMMARIES: dict[str, dict[str, str]] = {
    "local": {
        "runtime_profile": "Local",
        "agent_orchestration": "LangGraph / Native",
        "llm": "Ollama",
        "embeddings": "Ollama",
        "vector_store": "ChromaDB",
        "business_store": "SQLite",
        "object_store": "Local filesystem",
        "secrets": "Environment variables",
        "observability": "Python logging",
    },
    "oci": {
        "runtime_profile": "OCI",
        "agent_orchestration": "Native or OCI Responses API",
        "llm": "OCI Generative AI",
        "embeddings": "OCI Generative AI Embeddings",
        "vector_store": "Oracle Database 23ai Vector Search or OCI OpenSearch",
        "business_store": "Autonomous Database or Oracle Database",
        "object_store": "OCI Object Storage",
        "secrets": "OCI Vault",
        "observability": "OCI Logging / Monitoring / APM",
    },
    "gcp": {
        "runtime_profile": "GCP",
        "agent_orchestration": "Native or Vertex Agent",
        "llm": "Vertex AI Gemini",
        "embeddings": "Vertex AI Embeddings",
        "vector_store": "Vertex AI Vector Search, AlloyDB vector, or pgvector",
        "business_store": "Cloud SQL PostgreSQL or AlloyDB",
        "object_store": "Cloud Storage",
        "secrets": "Secret Manager",
        "observability": "Cloud Logging / Monitoring / Trace",
    },
    "generic-kubernetes": {
        "runtime_profile": "Generic Kubernetes",
        "agent_orchestration": "Native",
        "llm": "OpenAI-compatible or configured provider",
        "embeddings": "configured embedding provider",
        "vector_store": "pgvector, OpenSearch, or configured vector store",
        "business_store": "PostgreSQL",
        "object_store": "S3-compatible object storage",
        "secrets": "Kubernetes Secrets or External Secrets",
        "observability": "OpenTelemetry",
    },
}

PROVIDER_DISPLAY_NAMES = {
    "agent_orchestrator": {
        "langgraph": "LangGraph",
        "native": "Native",
        "oci_responses_api": "OCI Responses API",
        "vertex_agent": "Vertex Agent",
    },
    "llm_provider": {
        "fallback": "fallback",
        "ollama": "Ollama",
        "oci_genai": "OCI Generative AI",
        "vertex_ai": "Vertex AI Gemini",
    },
    "embedding_provider": {
        "ollama": "Ollama",
        "oci_genai": "OCI Generative AI Embeddings",
        "vertex_ai": "Vertex AI Embeddings",
    },
    "vector_store_provider": {
        "chroma": "ChromaDB",
        "oracle_23ai": "Oracle Database 23ai Vector Search",
        "vertex_vector_search": "Vertex AI Vector Search",
        "pgvector": "pgvector",
        "opensearch": "OpenSearch",
        "alloydb_vector": "AlloyDB vector",
    },
    "business_store_provider": {
        "sqlite": "SQLite",
        "oracle_autonomous_db": "Autonomous Database",
        "cloud_sql_postgres": "Cloud SQL PostgreSQL",
        "alloydb": "AlloyDB",
        "postgres": "PostgreSQL",
    },
    "object_store_provider": {
        "local_fs": "Local filesystem",
        "oci_object_storage": "OCI Object Storage",
        "gcs": "Cloud Storage",
        "s3_compatible": "S3-compatible object storage",
    },
    "secrets_provider": {
        "env": "Environment variables",
        "oci_vault": "OCI Vault",
        "gcp_secret_manager": "Secret Manager",
    },
    "observability_provider": {
        "python_logging": "Python logging",
        "oci_logging": "OCI Logging / Monitoring / APM",
        "gcp_logging": "Cloud Logging / Monitoring / Trace",
        "opentelemetry": "OpenTelemetry",
    },
}


@dataclass(frozen=True)
class PlatformConfig:
    """Configured provider names for one runtime profile."""

    platform_profile: str
    agent_orchestrator: str
    llm_provider: str
    embedding_provider: str
    vector_store_provider: str
    business_store_provider: str
    object_store_provider: str
    secrets_provider: str
    observability_provider: str


def get_platform_config() -> PlatformConfig:
    """Read provider selection from environment variables with local-safe defaults."""
    profile = os.getenv("PLATFORM_PROFILE", "local").strip().lower() or "local"
    if profile not in PROFILE_PROVIDER_DEFAULTS:
        supported = ", ".join(sorted(PROFILE_PROVIDER_DEFAULTS))
        raise ValueError(
            f"Unsupported PLATFORM_PROFILE={profile!r}. Supported profiles: {supported}."
        )

    defaults = PROFILE_PROVIDER_DEFAULTS[profile]
    return PlatformConfig(
        platform_profile=profile,
        agent_orchestrator=_provider_value("AGENT_ORCHESTRATOR", defaults),
        llm_provider=_provider_value("LLM_PROVIDER", defaults),
        embedding_provider=_provider_value("EMBEDDING_PROVIDER", defaults),
        vector_store_provider=_provider_value("VECTOR_STORE_PROVIDER", defaults),
        business_store_provider=_provider_value("BUSINESS_STORE_PROVIDER", defaults),
        object_store_provider=_provider_value("OBJECT_STORE_PROVIDER", defaults),
        secrets_provider=_provider_value("SECRETS_PROVIDER", defaults),
        observability_provider=_provider_value("OBSERVABILITY_PROVIDER", defaults),
    )


def get_runtime_profile_payload(config: PlatformConfig | None = None) -> dict[str, Any]:
    """Build a read-only runtime profile response without exposing secrets."""
    platform_config = config or get_platform_config()
    # Return provider names and display labels, never credential-bearing settings.
    return {
        "platform_profile": platform_config.platform_profile,
        "display_name": PROFILE_DISPLAY_SUMMARIES[platform_config.platform_profile][
            "runtime_profile"
        ],
        "agent_orchestrator": platform_config.agent_orchestrator,
        "llm_provider": platform_config.llm_provider,
        "embedding_provider": platform_config.embedding_provider,
        "vector_store_provider": platform_config.vector_store_provider,
        "business_store_provider": platform_config.business_store_provider,
        "object_store_provider": platform_config.object_store_provider,
        "secrets_provider": platform_config.secrets_provider,
        "observability_provider": platform_config.observability_provider,
        "editable_in_ui": False,
        "summary": _active_profile_summary(platform_config),
        "profiles": PROFILE_DISPLAY_SUMMARIES,
    }


def _provider_value(env_name: str, defaults: dict[str, str]) -> str:
    """Return one normalized provider setting."""
    key = env_name.lower()
    value = os.getenv(env_name, defaults[key]).strip().lower()
    return value or defaults[key]


def _active_profile_summary(config: PlatformConfig) -> dict[str, str]:
    """Return display labels for the currently selected provider values."""
    profile_summary = dict(PROFILE_DISPLAY_SUMMARIES[config.platform_profile])
    if config.platform_profile != "local":
        return profile_summary

    profile_summary.update(
        {
            "llm": _provider_display("llm_provider", config.llm_provider),
            "embeddings": _provider_display(
                "embedding_provider",
                config.embedding_provider,
            ),
            "vector_store": _provider_display(
                "vector_store_provider",
                config.vector_store_provider,
            ),
            "business_store": _provider_display(
                "business_store_provider",
                config.business_store_provider,
            ),
            "object_store": _provider_display(
                "object_store_provider",
                config.object_store_provider,
            ),
            "secrets": _provider_display("secrets_provider", config.secrets_provider),
            "observability": _provider_display(
                "observability_provider",
                config.observability_provider,
            ),
        }
    )
    return profile_summary


def _provider_display(provider_group: str, provider_name: str) -> str:
    """Return a safe display name for one provider setting."""
    return PROVIDER_DISPLAY_NAMES.get(provider_group, {}).get(
        provider_name,
        provider_name,
    )
