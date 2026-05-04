"""Test coverage for rag behavior.

Author: Sarala Biswal
"""

import json

import httpx
import pytest

from services.mcp import MCPExecutionEngine, ToolRegistry
from services.mcp.tools import register_rag_tools, search_knowledge
from services.embeddings import (
    EmbeddingClientError,
    OllamaEmbeddingClient,
    ProviderEmbeddingClient,
    create_embedding_client,
)
from services.platform.config import PlatformConfig
from services.rag import (
    ChromaVectorStore,
    ProviderVectorStore,
    Retriever,
    VectorStoreError,
    create_vector_store,
)
from services.rag.ingest import SAMPLE_DOCUMENTS, ingest_sample_documents


class FakeEmbeddingClient:
    """Verify fake embedding client behavior."""
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Verify embed behavior."""
        return [_fake_embedding(text) for text in texts]


class FakeRetriever:
    """Verify fake retriever behavior."""
    def __init__(self) -> None:
        """Verify   init   behavior."""
        self.calls: list[tuple[str, int]] = []

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        """Verify retrieve behavior."""
        self.calls.append((query, k))
        return ["Sales playbook context", "Pricing rules context"][:k]


def test_embedding_client_calls_ollama_embeddings_api() -> None:
    """Verify embedding client calls ollama embeddings api behavior."""
    captured_payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        """Verify handler behavior."""
        captured_payloads.append(json.loads(request.content))
        return httpx.Response(200, json={"embedding": [0.1, 0.2, 0.3]})

    client = OllamaEmbeddingClient(
        model="nomic-embed-text",
        base_url="http://ollama.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    embeddings = client.embed(["pricing rules"])

    assert captured_payloads == [
        {
            "model": "nomic-embed-text",
            "prompt": "pricing rules",
        }
    ]
    assert embeddings == [[0.1, 0.2, 0.3]]


def test_embedding_client_raises_for_missing_embedding() -> None:
    """Verify embedding client raises for missing embedding behavior."""
    def handler(_request: httpx.Request) -> httpx.Response:
        """Verify handler behavior."""
        return httpx.Response(200, json={"done": True})

    client = OllamaEmbeddingClient(
        base_url="http://ollama.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(EmbeddingClientError, match="did not include an embedding"):
        client.embed(["pricing rules"])


def test_ingestion_persists_sample_documents(tmp_path) -> None:
    """Verify ingestion persists sample documents behavior."""
    store = ChromaVectorStore(persist_directory=tmp_path / "chroma_db")

    count = ingest_sample_documents(
        embedding_client=FakeEmbeddingClient(),  # type: ignore[arg-type]
        vector_store=store,
    )

    reopened_store = ChromaVectorStore(persist_directory=tmp_path / "chroma_db")
    results = reopened_store.query(_fake_embedding("pricing rules"), n_results=2)

    assert count == len(SAMPLE_DOCUMENTS)
    assert len(results) == 2
    assert any("Pricing rules" in result for result in results)


def test_retriever_returns_list_from_vector_store(tmp_path) -> None:
    """Verify retriever returns list from vector store behavior."""
    store = ChromaVectorStore(persist_directory=tmp_path / "chroma_db")
    ingest_sample_documents(
        embedding_client=FakeEmbeddingClient(),  # type: ignore[arg-type]
        vector_store=store,
    )
    retriever = Retriever(
        embedding_client=FakeEmbeddingClient(),  # type: ignore[arg-type]
        vector_store=store,
    )

    results = retriever.retrieve("pricing rules", k=3)

    assert isinstance(results, list)
    assert any("Pricing rules" in result for result in results)


def test_vector_store_validates_input_lengths(tmp_path) -> None:
    """Verify vector store validates input lengths behavior."""
    store = ChromaVectorStore(persist_directory=tmp_path / "chroma_db")

    with pytest.raises(VectorStoreError, match="same length"):
        store.add_documents(ids=["one"], documents=["one"], embeddings=[])


def test_embedding_factory_selects_ollama_for_local_profile(monkeypatch) -> None:
    """Verify embedding factory keeps the local Ollama provider."""
    monkeypatch.setenv("PLATFORM_PROFILE", "local")
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)

    client = create_embedding_client()

    assert isinstance(client, OllamaEmbeddingClient)
    client.close()


def test_embedding_factory_returns_cloud_provider_stub() -> None:
    """Verify cloud embedding providers are explicit stubs."""
    client = create_embedding_client(config=_platform_config(embedding_provider="oci_genai"))

    assert isinstance(client, ProviderEmbeddingClient)
    with pytest.raises(NotImplementedError, match="EMBEDDING_PROVIDER"):
        client.embed(["hello"])


def test_vector_store_factory_selects_chroma_for_local_profile(monkeypatch) -> None:
    """Verify vector store factory keeps Chroma as the local provider."""
    monkeypatch.setenv("PLATFORM_PROFILE", "local")
    monkeypatch.delenv("VECTOR_STORE_PROVIDER", raising=False)

    store = create_vector_store()

    assert isinstance(store, ChromaVectorStore)


def test_vector_store_factory_returns_cloud_provider_stub() -> None:
    """Verify cloud vector stores are explicit stubs."""
    store = create_vector_store(config=_platform_config(vector_store_provider="oracle_23ai"))

    assert isinstance(store, ProviderVectorStore)
    with pytest.raises(NotImplementedError, match="VECTOR_STORE_PROVIDER"):
        store.query([0.1, 0.2], n_results=1)


def test_mcp_search_knowledge_tool_returns_structured_output() -> None:
    """Verify mcp search knowledge tool returns structured output behavior."""
    retriever = FakeRetriever()

    result = search_knowledge("sales playbook", k=2, retriever=retriever)  # type: ignore[arg-type]

    assert result == {
        "query": "sales playbook",
        "results": ["Sales playbook context", "Pricing rules context"],
    }
    assert retriever.calls == [("sales playbook", 2)]


def test_registered_mcp_rag_tool_executes_through_engine() -> None:
    """Verify registered mcp rag tool executes through engine behavior."""
    registry = ToolRegistry()
    register_rag_tools(registry, retriever_factory=lambda: FakeRetriever())  # type: ignore[arg-type]
    engine = MCPExecutionEngine(registry)

    result = engine.execute("search_knowledge", {"query": "pricing rules", "k": 1})

    assert result == {
        "query": "pricing rules",
        "results": ["Sales playbook context"],
    }


def _fake_embedding(text: str) -> list[float]:
    """Verify  fake embedding behavior."""
    normalized = text.lower()
    if "pricing" in normalized:
        return [1.0, 0.0, 0.0]
    if "playbook" in normalized:
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]


def _platform_config(
    embedding_provider: str = "ollama",
    vector_store_provider: str = "chroma",
) -> PlatformConfig:
    """Build provider config for RAG factory tests."""
    return PlatformConfig(
        platform_profile="local",
        agent_orchestrator="langgraph",
        llm_provider="fallback",
        embedding_provider=embedding_provider,
        vector_store_provider=vector_store_provider,
        business_store_provider="sqlite",
        object_store_provider="local_fs",
        secrets_provider="env",
        observability_provider="python_logging",
    )
