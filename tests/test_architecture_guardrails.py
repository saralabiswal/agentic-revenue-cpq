"""Test coverage for architecture guardrails behavior.

Author: Sarala Biswal
"""

import ast
from pathlib import Path

from schemas.chat import ChatRequest, ChatResponse
from schemas.quote import (
    ActivityListResponse,
    PricingRequest,
    QuoteCreateRequest,
    QuoteCreateResponse,
    QuoteFinalizeRequest,
    QuoteHistoryResponse,
    RecommendationRequest,
)
from services.agent import LangGraphAgentOrchestrator, create_agent_orchestrator
from services.business import SQLiteBusinessStore, create_business_store
from services.embeddings import OllamaEmbeddingClient, create_embedding_client
from services.platform import (
    EnvSecretsProvider,
    LocalFilesystemObjectStore,
    PythonLoggingObservabilityProvider,
    create_object_store,
    create_observability_provider,
    create_secrets_provider,
)
from services.rag import ChromaVectorStore, create_vector_store


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_agent_does_not_import_integrations_directly() -> None:
    """Verify agent does not import integrations directly behavior."""
    for path in (PROJECT_ROOT / "services" / "agent").glob("*.py"):
        source = path.read_text()

        assert "from integrations" not in source
        assert "import integrations" not in source


def test_agent_does_not_import_provider_or_vector_clients_directly() -> None:
    """Verify agent modules do not import integration, cloud, LLM, or vector clients."""
    forbidden_roots = {
        "chromadb",
        "google",
        "integrations",
        "oci",
        "ollama",
        "vertexai",
    }
    forbidden_modules = {
        "services.data",
        "services.rag",
        "services.llm.ollama",
        "services.rag.vector_store",
    }
    for path in (PROJECT_ROOT / "services" / "agent").glob("*.py"):
        tree = ast.parse(path.read_text())
        imported_modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)

        for module in imported_modules:
            assert module.split(".")[0] not in forbidden_roots
            assert module not in forbidden_modules


def test_agent_does_not_call_llm_providers_directly() -> None:
    """Verify agent does not call llm providers directly behavior."""
    for path in (PROJECT_ROOT / "services" / "agent").glob("*.py"):
        source = path.read_text()

        assert "OllamaClient" not in source
        assert "httpx" not in source
        assert "/api/chat" not in source


def test_agent_does_not_import_rag_directly() -> None:
    """Verify agent does not import rag directly behavior."""
    for path in (PROJECT_ROOT / "services" / "agent").glob("*.py"):
        source = path.read_text()

        assert "from services.rag" not in source
        assert "import services.rag" not in source
        assert "chromadb" not in source
        assert "/api/embeddings" not in source


def test_backend_routes_through_agent_not_tools_or_integrations() -> None:
    """Verify backend routes through agent not tools or integrations behavior."""
    source = (PROJECT_ROOT / "apps" / "backend" / "main.py").read_text()

    assert "from services.agent" in source
    assert "from integrations" not in source
    assert "from services.tools" not in source
    assert "OllamaClient" not in source


def test_tool_wrappers_are_the_integration_boundary() -> None:
    """Verify tool wrappers are the integration boundary behavior."""
    source = (PROJECT_ROOT / "services" / "tools" / "opportunity_quote.py").read_text()

    assert "from integrations.cpq" in source
    assert "from integrations.salesforce" in source
    assert "ToolDefinition" in source


def test_rag_is_exposed_only_through_mcp_tool() -> None:
    """Verify rag is exposed only through mcp tool behavior."""
    source = (PROJECT_ROOT / "services" / "mcp" / "tools" / "rag_tools.py").read_text()

    assert "from services.rag" in source
    assert 'name="search_knowledge"' in source


def test_agent_rag_access_is_only_mcp_search_knowledge() -> None:
    """Verify agent RAG access remains a named MCP tool call."""
    agent_sources = "\n".join(
        path.read_text() for path in (PROJECT_ROOT / "services" / "agent").glob("*.py")
    )

    assert '"search_knowledge"' in agent_sources
    assert "from services.rag" not in agent_sources
    assert "import services.rag" not in agent_sources


def test_llm_usage_goes_through_llm_client_boundary() -> None:
    """Verify agent code depends on the LLM interface instead of provider clients."""
    agent_sources = "\n".join(
        path.read_text() for path in (PROJECT_ROOT / "services" / "agent").glob("*.py")
    )

    assert "LLMClient" in agent_sources
    assert "OllamaClient" not in agent_sources
    assert "oci_genai" not in agent_sources
    assert "vertex_ai" not in agent_sources


def test_platform_profile_local_preserves_provider_defaults(monkeypatch, tmp_path) -> None:
    """Verify local profile selects local providers and needs no cloud credentials."""
    for env_name in [
        "PLATFORM_PROFILE",
        "AGENT_ORCHESTRATOR",
        "EMBEDDING_PROVIDER",
        "VECTOR_STORE_PROVIDER",
        "BUSINESS_STORE_PROVIDER",
        "OBJECT_STORE_PROVIDER",
        "SECRETS_PROVIDER",
        "OBSERVABILITY_PROVIDER",
    ]:
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setenv("OBJECT_STORE_PATH", str(tmp_path / "objects"))

    assert isinstance(create_agent_orchestrator(), LangGraphAgentOrchestrator)
    assert isinstance(create_embedding_client(), OllamaEmbeddingClient)
    assert isinstance(create_vector_store(), ChromaVectorStore)
    assert isinstance(create_business_store(), SQLiteBusinessStore)
    assert isinstance(create_object_store(), LocalFilesystemObjectStore)
    assert isinstance(create_secrets_provider(), EnvSecretsProvider)
    assert isinstance(create_observability_provider(), PythonLoggingObservabilityProvider)


def test_api_schemas_keep_source_prefixed_external_ids() -> None:
    """Verify API schemas expose source-owned IDs instead of generic external IDs."""
    schema_models = [
        ChatRequest,
        ChatResponse,
        ActivityListResponse,
        RecommendationRequest,
        PricingRequest,
        QuoteCreateRequest,
        QuoteCreateResponse,
        QuoteHistoryResponse,
        QuoteFinalizeRequest,
    ]
    field_names = {
        field_name
        for model in schema_models
        for field_name in model.model_fields
    }

    assert "sf_opportunity_id" in field_names
    assert "oracle_quote_id" in field_names
    assert "account_id" not in field_names
    assert "opportunity_id" not in field_names
    assert "quote_id" not in field_names
    assert "order_id" not in field_names


def test_cloud_sdk_imports_do_not_leak_into_core_python_modules() -> None:
    """Verify cloud SDK imports, if added later, stay out of core modules."""
    forbidden_roots = {"oci", "google", "vertexai"}
    allowed_path_parts = {"providers", "oci", "gcp"}
    for path in _python_source_files():
        if allowed_path_parts.intersection(path.parts):
            continue
        tree = ast.parse(path.read_text())
        imported_roots: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.extend(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.append(node.module.split(".")[0])

        assert not forbidden_roots.intersection(imported_roots), str(path)


def test_deployment_profile_docs_exist_and_preserve_local_default() -> None:
    """Verify cloud deployment docs are provider profiles, not core dependencies."""
    oci_doc = (PROJECT_ROOT / "docs" / "architecture" / "oci-deployment-profile.md")
    gcp_doc = (PROJECT_ROOT / "docs" / "architecture" / "gcp-deployment-profile.md")

    assert oci_doc.exists()
    assert gcp_doc.exists()
    assert "PLATFORM_PROFILE=oci" in oci_doc.read_text()
    assert "PLATFORM_PROFILE=gcp" in gcp_doc.read_text()
    assert "local Docker Compose application remains the default" in oci_doc.read_text()
    assert "local Docker Compose application remains the default" in gcp_doc.read_text()


def _python_source_files() -> list[Path]:
    """Return project Python files excluding caches and tests."""
    roots = [
        PROJECT_ROOT / "apps",
        PROJECT_ROOT / "configs",
        PROJECT_ROOT / "integrations",
        PROJECT_ROOT / "schemas",
        PROJECT_ROOT / "services",
    ]
    files: list[Path] = []
    for root in roots:
        files.extend(
            path
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts
        )
    return files
