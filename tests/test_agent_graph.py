"""Test coverage for agent graph behavior.

Author: Sarala Biswal
"""

from services.agent import build_agent_graph
from services.llm import LLMClient


def test_agent_graph_runs_opportunity_to_quote_flow() -> None:
    """Verify agent graph runs opportunity to quote flow behavior."""
    graph = build_agent_graph()

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
    assert result["intent"] == "opportunity_to_quote"
    assert result["sf_opportunity_id"] == "SF-OPP-001"
    assert result["opportunity"]["sf_opportunity_id"] == "SF-OPP-001"
    assert result["pricing"]["total"] == 1572500.0
    assert result["quote"]["oracle_quote_id"] == "ORA-Q-001-001"
    assert "Created draft quote ORA-Q-001-001" in result["response"]["message"]
    assert result["response"]["oracle_quote_id"] == "ORA-Q-001-001"


def test_agent_graph_uses_default_opportunity_id_for_demo_flow() -> None:
    """Verify agent graph uses default opportunity id for demo flow behavior."""
    graph = build_agent_graph()

    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Recommend products and create a quote"}]}
    )

    assert result["sf_opportunity_id"] == "SF-OPP-001"
    assert result["quote"]["oracle_quote_id"] == "ORA-Q-001-001"


def test_agent_graph_executes_tools_in_expected_mcp_order() -> None:
    """Verify agent graph executes tools in expected mcp order behavior."""
    class RecordingEngine:
        """Verify recording engine behavior."""
        def __init__(self) -> None:
            """Verify   init   behavior."""
            self.calls: list[tuple[str, dict]] = []

        def execute(self, tool_name: str, payload: dict | None = None) -> dict:
            """Verify execute behavior."""
            self.calls.append((tool_name, payload or {}))
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
                    "oracle_quote_id": "ORA-Q-123-001",
                    "sf_opportunity_id": payload["pricing"]["sf_opportunity_id"],
                }
            raise AssertionError(f"Unexpected tool: {tool_name}")

    engine = RecordingEngine()
    graph = build_agent_graph(engine)  # type: ignore[arg-type]

    result = graph.invoke({"sf_opportunity_id": "SF-OPP-123"})

    assert [call[0] for call in engine.calls] == [
        "get_opportunity",
        "recommend_products",
        "get_pricing",
        "create_quote",
    ]
    assert result["response"]["oracle_quote_id"] == "ORA-Q-123-001"


def test_agent_graph_generates_response_through_llm_client() -> None:
    """Verify agent graph generates response through llm client behavior."""
    class RecordingLLMClient(LLMClient):
        """Verify recording l l m client behavior."""
        def __init__(self) -> None:
            """Verify   init   behavior."""
            self.messages: list[dict] | None = None

        def chat(self, messages: list[dict]) -> dict:
            """Run the full chat-driven opportunity-to-quote workflow."""
            self.messages = messages
            return {
                "role": "assistant",
                "content": "Recommended products and created quote ORA-Q-001-001.",
            }

    llm_client = RecordingLLMClient()
    graph = build_agent_graph(llm_client=llm_client)

    result = graph.invoke({"sf_opportunity_id": "SF-OPP-001"})

    assert llm_client.messages is not None
    assert llm_client.messages[0]["role"] == "system"
    assert "AFF A-Series Performance Storage" in llm_client.messages[1]["content"]
    assert "ORA-Q-001-001" in llm_client.messages[1]["content"]
    assert result["assistant_message"] == {
        "role": "assistant",
        "content": "Recommended products and created quote ORA-Q-001-001.",
    }
    assert result["response"]["message"] == (
        "Recommended products and created quote ORA-Q-001-001."
    )


def test_agent_graph_retrieves_context_through_mcp_and_augments_llm_prompt() -> None:
    """Verify agent graph retrieves context through mcp and augments llm prompt behavior."""
    class RecordingEngine:
        """Verify recording engine behavior."""
        def __init__(self) -> None:
            """Verify   init   behavior."""
            self.calls: list[tuple[str, dict]] = []

        def execute(self, tool_name: str, payload: dict | None = None) -> dict:
            """Verify execute behavior."""
            self.calls.append((tool_name, payload or {}))
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
                    "oracle_quote_id": "ORA-Q-123-001",
                    "sf_opportunity_id": payload["pricing"]["sf_opportunity_id"],
                }
            raise AssertionError(f"Unexpected tool: {tool_name}")

    class RecordingLLMClient(LLMClient):
        """Verify recording l l m client behavior."""
        def __init__(self) -> None:
            """Verify   init   behavior."""
            self.messages: list[dict] | None = None

        def chat(self, messages: list[dict]) -> dict:
            """Run the full chat-driven opportunity-to-quote workflow."""
            self.messages = messages
            return {
                    "role": "assistant",
                    "content": "Used playbook context and created ORA-Q-123-001.",
                }

    engine = RecordingEngine()
    llm_client = RecordingLLMClient()
    graph = build_agent_graph(engine, llm_client=llm_client)  # type: ignore[arg-type]

    result = graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Use the sales playbook for SF-OPP-123 and create a quote",
                }
            ]
        }
    )

    assert [call[0] for call in engine.calls] == [
        "search_knowledge",
        "get_opportunity",
        "recommend_products",
        "get_pricing",
        "create_quote",
    ]
    assert result["retrieved_context"] == ["Sales playbook: include quote id and total."]
    assert result["tools_output"]["quote"]["oracle_quote_id"] == "ORA-Q-123-001"
    assert result["final_answer"] == "Used playbook context and created ORA-Q-123-001."
    assert llm_client.messages is not None
    assert llm_client.messages[1]["content"] == (
        "CONTEXT:\nSales playbook: include quote id and total."
    )
    assert "USER:\nUse the sales playbook" in llm_client.messages[2]["content"]
