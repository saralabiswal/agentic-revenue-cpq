"""Test coverage for AgentOrchestrator implementations and factory selection.

Author: Sarala Biswal
"""

import pytest

from services.agent import (
    LangGraphAgentOrchestrator,
    NativeAgentOrchestrator,
    ProviderManagedAgentOrchestrator,
    create_agent_orchestrator,
)
from services.platform.config import PlatformConfig


def _config(agent_orchestrator: str) -> PlatformConfig:
    """Build a minimal platform config for orchestrator factory tests."""
    return PlatformConfig(
        platform_profile="local",
        agent_orchestrator=agent_orchestrator,
        llm_provider="fallback",
        embedding_provider="ollama",
        vector_store_provider="chroma",
        business_store_provider="sqlite",
        object_store_provider="local_fs",
        secrets_provider="env",
        observability_provider="python_logging",
    )


def test_agent_orchestrator_factory_selects_langgraph_default(monkeypatch) -> None:
    """Verify factory selects LangGraph for the local default profile."""
    monkeypatch.delenv("PLATFORM_PROFILE", raising=False)
    monkeypatch.delenv("AGENT_ORCHESTRATOR", raising=False)

    orchestrator = create_agent_orchestrator()

    assert isinstance(orchestrator, LangGraphAgentOrchestrator)


def test_agent_orchestrator_factory_selects_native() -> None:
    """Verify factory can select the native Python orchestrator."""
    orchestrator = create_agent_orchestrator(config=_config("native"))

    assert isinstance(orchestrator, NativeAgentOrchestrator)


def test_agent_orchestrator_factory_returns_provider_stubs() -> None:
    """Verify provider-managed orchestrators are explicit stubs for now."""
    orchestrator = create_agent_orchestrator(config=_config("oci_responses_api"))

    assert isinstance(orchestrator, ProviderManagedAgentOrchestrator)
    with pytest.raises(NotImplementedError, match="is a stub"):
        orchestrator.run_chat({})


def test_native_orchestrator_runs_same_recommendation_flow_as_langgraph() -> None:
    """Verify native orchestration preserves the current recommendation behavior."""
    state = {
        "sf_opportunity_id": "SF-OPP-001",
        "messages": [{"role": "user", "content": "Recommend products for review"}],
    }

    langgraph_result = LangGraphAgentOrchestrator().run_recommendation(state)
    native_result = NativeAgentOrchestrator().run_recommendation(state)

    assert native_result["status"] == langgraph_result["status"] == "ready_for_review"
    assert native_result["sf_opportunity_id"] == "SF-OPP-001"
    assert native_result["pricing"]["total"] == langgraph_result["pricing"]["total"]
    assert native_result["response"]["products"] == langgraph_result["response"]["products"]
    assert [step["id"] for step in native_result["run_steps"]] == [
        "analyze",
        "retrieve_context",
        "get_opportunity",
        "recommend_products",
        "get_pricing",
    ]


def test_native_orchestrator_runs_quote_creation_flow() -> None:
    """Verify native orchestration can price selections and create a quote."""
    recommendation = NativeAgentOrchestrator().run_recommendation(
        {
            "sf_opportunity_id": "SF-OPP-001",
            "messages": [{"role": "user", "content": "Recommend products"}],
        }
    )

    result = NativeAgentOrchestrator().run_quote_creation(
        {
            "sf_opportunity_id": "SF-OPP-001",
            "currency": "USD",
            "selected_products": recommendation["response"]["products"],
            "persist_quote": True,
        }
    )

    assert result["status"] == "completed"
    assert result["response"]["oracle_quote_id"] == "ORA-Q-001-001"
    assert result["response"]["quote"]["selected_product_count"] == 7
