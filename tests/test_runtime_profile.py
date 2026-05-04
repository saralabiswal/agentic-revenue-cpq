"""Test coverage for runtime provider profile visibility.

Author: Sarala Biswal
"""

from fastapi.testclient import TestClient

from apps.backend.main import app


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


def test_runtime_profile_defaults_to_local(monkeypatch) -> None:
    """Verify default runtime profile response is local and read-only."""
    for env_name in PROVIDER_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)
    client = TestClient(app)

    response = client.get("/runtime/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["platform_profile"] == "local"
    assert body["display_name"] == "Local"
    assert body["agent_orchestrator"] == "langgraph"
    assert body["llm_provider"] == "ollama"
    assert body["embedding_provider"] == "ollama"
    assert body["vector_store_provider"] == "chroma"
    assert body["business_store_provider"] == "sqlite"
    assert body["object_store_provider"] == "local_fs"
    assert body["secrets_provider"] == "env"
    assert body["observability_provider"] == "python_logging"
    assert body["editable_in_ui"] is False
    assert body["summary"] == {
        "runtime_profile": "Local",
        "agent_orchestration": "LangGraph / Native",
        "llm": "Ollama",
        "embeddings": "Ollama",
        "vector_store": "ChromaDB",
        "business_store": "SQLite",
        "object_store": "Local filesystem",
        "secrets": "Environment variables",
        "observability": "Python logging",
    }
    assert set(body["profiles"]) == {"local", "oci", "gcp", "generic-kubernetes"}


def test_runtime_profile_local_ollama_display(monkeypatch) -> None:
    """Verify local LLM display follows configured local provider."""
    monkeypatch.setenv("PLATFORM_PROFILE", "local")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    client = TestClient(app)

    response = client.get("/runtime/profile")

    assert response.status_code == 200
    assert response.json()["llm_provider"] == "ollama"
    assert response.json()["summary"]["llm"] == "Ollama"


def test_runtime_profile_oci_display_mapping(monkeypatch) -> None:
    """Verify OCI profile response uses OCI display mappings only."""
    monkeypatch.setenv("PLATFORM_PROFILE", "oci")
    client = TestClient(app)

    response = client.get("/runtime/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["platform_profile"] == "oci"
    assert body["display_name"] == "OCI"
    assert body["llm_provider"] == "oci_genai"
    assert body["summary"]["llm"] == "OCI Generative AI"
    assert body["summary"]["vector_store"] == (
        "Oracle Database 23ai Vector Search or OCI OpenSearch"
    )
    assert body["summary"]["business_store"] == "Autonomous Database or Oracle Database"
    assert body["summary"]["secrets"] == "OCI Vault"


def test_runtime_profile_gcp_display_mapping(monkeypatch) -> None:
    """Verify GCP profile response uses GCP display mappings only."""
    monkeypatch.setenv("PLATFORM_PROFILE", "gcp")
    client = TestClient(app)

    response = client.get("/runtime/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["platform_profile"] == "gcp"
    assert body["display_name"] == "GCP"
    assert body["llm_provider"] == "vertex_ai"
    assert body["summary"]["llm"] == "Vertex AI Gemini"
    assert body["summary"]["vector_store"] == (
        "Vertex AI Vector Search, AlloyDB vector, or pgvector"
    )
    assert body["summary"]["business_store"] == "Cloud SQL PostgreSQL or AlloyDB"
    assert body["summary"]["observability"] == "Cloud Logging / Monitoring / Trace"


def test_runtime_profile_does_not_expose_sensitive_config(monkeypatch) -> None:
    """Verify runtime profile omits secrets, tokens, URLs, and connection strings."""
    monkeypatch.setenv("PLATFORM_PROFILE", "local")
    monkeypatch.setenv("DATABASE_URL", "postgres://user:password@example/db")
    monkeypatch.setenv("API_TOKEN", "secret-token")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://credential-bearing.example")
    client = TestClient(app)

    response = client.get("/runtime/profile")

    assert response.status_code == 200
    payload = response.text.lower()
    assert "secret-token" not in payload
    assert "password" not in payload
    assert "credential-bearing" not in payload
    assert "database_url" not in payload
    assert "api_token" not in payload
