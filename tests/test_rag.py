import json

import httpx
import pytest

from services.mcp import MCPExecutionEngine, ToolRegistry
from services.mcp.tools import register_rag_tools, search_knowledge
from services.rag import EmbeddingClient, EmbeddingClientError, Retriever, VectorStore, VectorStoreError
from services.rag.ingest import SAMPLE_DOCUMENTS, ingest_sample_documents


class FakeEmbeddingClient:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_fake_embedding(text) for text in texts]


class FakeRetriever:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        self.calls.append((query, k))
        return ["Sales playbook context", "Pricing rules context"][:k]


def test_embedding_client_calls_ollama_embeddings_api() -> None:
    captured_payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_payloads.append(json.loads(request.content))
        return httpx.Response(200, json={"embedding": [0.1, 0.2, 0.3]})

    client = EmbeddingClient(
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
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"done": True})

    client = EmbeddingClient(
        base_url="http://ollama.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(EmbeddingClientError, match="did not include an embedding"):
        client.embed(["pricing rules"])


def test_ingestion_persists_sample_documents(tmp_path) -> None:
    store = VectorStore(persist_directory=tmp_path / "chroma_db")

    count = ingest_sample_documents(
        embedding_client=FakeEmbeddingClient(),  # type: ignore[arg-type]
        vector_store=store,
    )

    reopened_store = VectorStore(persist_directory=tmp_path / "chroma_db")
    results = reopened_store.query(_fake_embedding("pricing rules"), n_results=2)

    assert count == len(SAMPLE_DOCUMENTS)
    assert len(results) == 2
    assert any("Pricing rules" in result for result in results)


def test_retriever_returns_list_from_vector_store(tmp_path) -> None:
    store = VectorStore(persist_directory=tmp_path / "chroma_db")
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
    store = VectorStore(persist_directory=tmp_path / "chroma_db")

    with pytest.raises(VectorStoreError, match="same length"):
        store.add_documents(ids=["one"], documents=["one"], embeddings=[])


def test_mcp_search_knowledge_tool_returns_structured_output() -> None:
    retriever = FakeRetriever()

    result = search_knowledge("sales playbook", k=2, retriever=retriever)  # type: ignore[arg-type]

    assert result == {
        "query": "sales playbook",
        "results": ["Sales playbook context", "Pricing rules context"],
    }
    assert retriever.calls == [("sales playbook", 2)]


def test_registered_mcp_rag_tool_executes_through_engine() -> None:
    registry = ToolRegistry()
    register_rag_tools(registry, retriever_factory=lambda: FakeRetriever())  # type: ignore[arg-type]
    engine = MCPExecutionEngine(registry)

    result = engine.execute("search_knowledge", {"query": "pricing rules", "k": 1})

    assert result == {
        "query": "pricing rules",
        "results": ["Sales playbook context"],
    }


def _fake_embedding(text: str) -> list[float]:
    normalized = text.lower()
    if "pricing" in normalized:
        return [1.0, 0.0, 0.0]
    if "playbook" in normalized:
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]
