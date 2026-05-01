"""Test coverage for logging behavior.

Author: Sarala Biswal
"""

import logging

import pytest
from fastapi.testclient import TestClient

from apps.backend.main import app
from configs import configure_logging
from services.agent import build_agent_graph
from services.mcp.tools import search_knowledge


class LoggingFakeEngine:
    """Verify logging fake engine behavior."""
    def __init__(self) -> None:
        """Verify   init   behavior."""
        self.calls: list[str] = []

    def execute(self, tool_name: str, payload: dict | None = None) -> dict:
        """Verify execute behavior."""
        self.calls.append(tool_name)
        payload = payload or {}
        if tool_name == "search_knowledge":
            return {
                "query": payload["query"],
                "results": ["Sales playbook: include quote id and total."],
            }
        if tool_name == "get_opportunity":
            return {"sf_opportunity_id": payload["sf_opportunity_id"]}
        if tool_name == "recommend_products":
            return {
                "sf_opportunity_id": payload["opportunity"]["sf_opportunity_id"],
                "products": [
                    {
                        "sku": "NTAP-AFF-A-SERIES",
                        "name": "AFF A-Series Performance Storage",
                    }
                ],
            }
        if tool_name == "get_pricing":
            return {
                "sf_opportunity_id": payload["recommendation"]["sf_opportunity_id"],
                "currency": "USD",
                "line_items": [{"sku": "NTAP-AFF-A-SERIES"}],
                "total": 75000.0,
            }
        if tool_name == "create_quote":
            return {
                "oracle_quote_id": "ORA-QUOTE-LOG-001",
                "sf_opportunity_id": payload["pricing"]["sf_opportunity_id"],
            }
        raise AssertionError(f"Unexpected tool: {tool_name}")


class LoggingFakeRetriever:
    """Verify logging fake retriever behavior."""
    def retrieve(self, query: str, k: int = 3) -> list[str]:
        """Verify retrieve behavior."""
        return ["Pricing rules context", "Sales playbook context"][:k]


def test_configure_logging_resolves_configured_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify configure logging resolves configured level behavior."""
    root_logger = logging.getLogger()
    previous_level = root_logger.level
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    try:
        resolved_level = configure_logging()
    finally:
        configure_logging(previous_level)

    assert resolved_level == logging.DEBUG


def test_backend_chat_logs_request_lifecycle(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify backend chat logs request lifecycle behavior."""
    client = TestClient(app)

    with caplog.at_level(logging.INFO, logger="apps.backend.main"):
        response = client.post(
            "/chat",
            json={"message": "Recommend products and create a quote for SF-OPP-001"},
        )

    assert response.status_code == 200
    assert "Chat request received" in caplog.text
    assert "message_length=" in caplog.text
    assert "Chat request completed" in caplog.text
    assert "oracle_quote_id=ORA-Q-001-001" in caplog.text


def test_agent_logs_rag_skip_decision(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify agent logs rag skip decision behavior."""
    engine = LoggingFakeEngine()
    graph = build_agent_graph(engine)  # type: ignore[arg-type]

    with caplog.at_level(logging.INFO, logger="services.agent.graph"):
        result = graph.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Recommend products and create a quote for SF-OPP-001",
                    }
                ]
            }
        )

    assert result["status"] == "completed"
    assert "Agent intent analyzed" in caplog.text
    assert "Agent RAG skipped: reason=no_domain_keyword" in caplog.text
    assert "search_knowledge" not in engine.calls


def test_agent_logs_rag_retrieval_decision(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify agent logs rag retrieval decision behavior."""
    engine = LoggingFakeEngine()
    graph = build_agent_graph(engine)  # type: ignore[arg-type]

    with caplog.at_level(logging.INFO, logger="services.agent.graph"):
        result = graph.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Use the sales playbook and create a quote for SF-OPP-001",
                    }
                ]
            }
        )

    assert result["retrieved_context"] == ["Sales playbook: include quote id and total."]
    assert "Agent requesting RAG context through MCP" in caplog.text
    assert "Agent RAG context retrieved: result_count=1" in caplog.text
    assert "search_knowledge" in engine.calls


def test_rag_tool_logs_search_result_count(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify rag tool logs search result count behavior."""
    with caplog.at_level(logging.INFO, logger="services.mcp.tools.rag_tools"):
        result = search_knowledge(
            "pricing rules",
            k=2,
            retriever=LoggingFakeRetriever(),  # type: ignore[arg-type]
        )

    assert result["results"] == ["Pricing rules context", "Sales playbook context"]
    assert "Searching knowledge base: query_length=13 k=2" in caplog.text
    assert "Knowledge search completed: result_count=2" in caplog.text
