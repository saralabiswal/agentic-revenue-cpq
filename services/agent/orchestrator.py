"""Cloud-agnostic agent orchestration boundary.

Author: Sarala Biswal
"""

from __future__ import annotations

import logging
from typing import Protocol

from services.agent import graph as graph_workflows
from services.agent.state import AgentState
from services.llm import LLMClient
from services.mcp import MCPExecutionEngine
from services.mcp.factory import create_default_mcp_engine
from services.platform import PlatformConfig, get_platform_config


logger = logging.getLogger(__name__)


class AgentOrchestrator(Protocol):
    """Interface for all agent workflow implementations."""

    def run_chat(self, state: AgentState) -> AgentState:
        """Run the full opportunity-to-quote workflow."""

    def run_recommendation(self, state: AgentState) -> AgentState:
        """Run recommendation and pricing without creating a quote."""

    def run_pricing(self, state: AgentState) -> AgentState:
        """Run selected-product pricing."""

    def run_quote_creation(self, state: AgentState) -> AgentState:
        """Run selected-product pricing and quote creation."""


class LangGraphAgentOrchestrator:
    """AgentOrchestrator implementation backed by the local/demo LangGraph flows."""

    def __init__(
        self,
        execution_engine: MCPExecutionEngine | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Create a LangGraph orchestrator using the configured MCP and LLM clients."""
        self._execution_engine = execution_engine
        self._llm_client = llm_client

    def run_chat(self, state: AgentState) -> AgentState:
        """Run the full LangGraph opportunity-to-quote workflow."""
        return graph_workflows.build_agent_graph(
            execution_engine=self._execution_engine,
            llm_client=self._llm_client,
        ).invoke(state)

    def run_recommendation(self, state: AgentState) -> AgentState:
        """Run the LangGraph recommendation workflow."""
        return graph_workflows.build_recommendation_graph(
            execution_engine=self._execution_engine,
            llm_client=self._llm_client,
        ).invoke(state)

    def run_pricing(self, state: AgentState) -> AgentState:
        """Run the LangGraph pricing workflow."""
        return graph_workflows.build_pricing_graph(
            execution_engine=self._execution_engine,
        ).invoke(state)

    def run_quote_creation(self, state: AgentState) -> AgentState:
        """Run the LangGraph quote creation workflow."""
        return graph_workflows.build_quote_creation_graph(
            execution_engine=self._execution_engine,
            llm_client=self._llm_client,
        ).invoke(state)


class NativeAgentOrchestrator:
    """AgentOrchestrator implementation that executes the workflow in plain Python."""

    def __init__(
        self,
        execution_engine: MCPExecutionEngine | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Create a native orchestrator using the same MCP and LLM boundaries."""
        self._execution_engine = execution_engine or create_default_mcp_engine()
        self._llm_client = llm_client

    def run_chat(self, state: AgentState) -> AgentState:
        """Run the full opportunity-to-quote workflow without LangGraph execution."""
        return self._run_steps(
            state,
            [
                graph_workflows._analyze_intent,
                graph_workflows._retrieve_context(self._execution_engine),
                graph_workflows._get_opportunity(self._execution_engine),
                graph_workflows._recommend_products(self._execution_engine),
                graph_workflows._get_pricing(self._execution_engine),
                graph_workflows._create_quote(self._execution_engine),
                graph_workflows._respond(self._llm_client),
            ],
        )

    def run_recommendation(self, state: AgentState) -> AgentState:
        """Run the recommendation workflow without LangGraph execution."""
        return self._run_steps(
            state,
            [
                graph_workflows._analyze_intent,
                graph_workflows._retrieve_context(self._execution_engine),
                graph_workflows._get_opportunity(self._execution_engine),
                graph_workflows._recommend_products(self._execution_engine),
                graph_workflows._get_pricing(self._execution_engine),
                graph_workflows._respond_recommendation(self._llm_client),
            ],
        )

    def run_pricing(self, state: AgentState) -> AgentState:
        """Run selected-product pricing without LangGraph execution."""
        return self._run_steps(
            state,
            [
                graph_workflows._prepare_selection_recommendation,
                graph_workflows._get_pricing(self._execution_engine),
                graph_workflows._respond_pricing,
            ],
        )

    def run_quote_creation(self, state: AgentState) -> AgentState:
        """Run selected-product quote creation without LangGraph execution."""
        return self._run_steps(
            state,
            [
                graph_workflows._prepare_selection_recommendation,
                graph_workflows._get_pricing(self._execution_engine),
                graph_workflows._create_quote(self._execution_engine),
                graph_workflows._respond_quote_creation(self._llm_client),
            ],
        )

    def _run_steps(self, state: AgentState, steps: list) -> AgentState:
        """Merge each workflow step's partial state like LangGraph does."""
        current: AgentState = dict(state)
        for step in steps:
            update = step(current)
            current.update(update)
        return current


class ProviderManagedAgentOrchestrator:
    """Placeholder for cloud-provider managed agent services."""

    def __init__(self, provider_name: str) -> None:
        """Store the provider name for clear runtime errors."""
        self._provider_name = provider_name

    def run_chat(self, state: AgentState) -> AgentState:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def run_recommendation(self, state: AgentState) -> AgentState:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def run_pricing(self, state: AgentState) -> AgentState:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def run_quote_creation(self, state: AgentState) -> AgentState:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def _not_implemented(self) -> NotImplementedError:
        """Build the clear stub error."""
        return NotImplementedError(
            f"Agent orchestrator provider {self._provider_name!r} is a stub. "
            "Use AGENT_ORCHESTRATOR=langgraph or AGENT_ORCHESTRATOR=native for local runs."
        )


def create_agent_orchestrator(
    config: PlatformConfig | None = None,
    execution_engine: MCPExecutionEngine | None = None,
    llm_client: LLMClient | None = None,
) -> AgentOrchestrator:
    """Create the configured AgentOrchestrator implementation."""
    platform_config = config or get_platform_config()
    provider = platform_config.agent_orchestrator
    logger.info(
        "Agent orchestrator selected: profile=%s provider=%s",
        platform_config.platform_profile,
        provider,
    )

    if provider == "langgraph":
        return LangGraphAgentOrchestrator(
            execution_engine=execution_engine,
            llm_client=llm_client,
        )
    if provider == "native":
        return NativeAgentOrchestrator(
            execution_engine=execution_engine,
            llm_client=llm_client,
        )
    if provider in {"oci_responses_api", "vertex_agent"}:
        return ProviderManagedAgentOrchestrator(provider)

    raise ValueError(
        f"Unsupported AGENT_ORCHESTRATOR={provider!r}. "
        "Supported values: langgraph, native, oci_responses_api, vertex_agent."
    )
