"""LangGraph workflows that orchestrate intent analysis, retrieval, MCP tools, and responses.

Author: Sarala Biswal
"""

import logging
import re

from langgraph.graph import END, START, StateGraph

from services.agent.state import AgentState
from services.llm import LLMClient
from services.mcp import MCPExecutionEngine
from services.tools import create_default_tool_registry


logger = logging.getLogger(__name__)

# Agent orchestration overview:
# - FastAPI builds the first AgentState dictionary and invokes one of these graphs.
# - Each graph node receives state, returns partial state, and LangGraph merges it.
# - Nodes never call Salesforce, CPQ, RAG, or SQLite directly; they call MCP tools.
# - Response nodes convert tool outputs into API payloads for the frontend.


# ---------------------------------------------------------------------------
# Graph builders.
# Each builder assembles a different workflow from the same small node functions.
# ---------------------------------------------------------------------------


def build_agent_graph(
    execution_engine: MCPExecutionEngine | None = None,
    llm_client: LLMClient | None = None,
):
    """Build the full opportunity-to-quote LangGraph workflow."""
    engine = execution_engine or MCPExecutionEngine(create_default_tool_registry())

    # Full chat flow: this is the most automated path and creates a draft quote.
    graph = StateGraph(AgentState)
    graph.add_node("analyze", _analyze_intent)
    graph.add_node("retrieve_context", _retrieve_context(engine))
    graph.add_node("get_opportunity", _get_opportunity(engine))
    graph.add_node("recommend_products", _recommend_products(engine))
    graph.add_node("get_pricing", _get_pricing(engine))
    graph.add_node("create_quote", _create_quote(engine))
    graph.add_node("respond", _respond(llm_client))

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "retrieve_context")
    graph.add_edge("retrieve_context", "get_opportunity")
    graph.add_edge("get_opportunity", "recommend_products")
    graph.add_edge("recommend_products", "get_pricing")
    graph.add_edge("get_pricing", "create_quote")
    graph.add_edge("create_quote", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


def build_recommendation_graph(
    execution_engine: MCPExecutionEngine | None = None,
    llm_client: LLMClient | None = None,
):
    """Build a recommendation-only LangGraph workflow for sales review."""
    engine = execution_engine or MCPExecutionEngine(create_default_tool_registry())

    # Review flow: stop before quote creation so the sales rep can edit selections.
    graph = StateGraph(AgentState)
    graph.add_node("analyze", _analyze_intent)
    graph.add_node("retrieve_context", _retrieve_context(engine))
    graph.add_node("get_opportunity", _get_opportunity(engine))
    graph.add_node("recommend_products", _recommend_products(engine))
    graph.add_node("get_pricing", _get_pricing(engine))
    graph.add_node("respond", _respond_recommendation(llm_client))

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "retrieve_context")
    graph.add_edge("retrieve_context", "get_opportunity")
    graph.add_edge("get_opportunity", "recommend_products")
    graph.add_edge("recommend_products", "get_pricing")
    graph.add_edge("get_pricing", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


def build_pricing_graph(execution_engine: MCPExecutionEngine | None = None):
    """Build a pricing-only graph for selected products."""
    engine = execution_engine or MCPExecutionEngine(create_default_tool_registry())

    # Repricing flow: frontend already has selected products, so recommendation is skipped.
    graph = StateGraph(AgentState)
    graph.add_node("prepare_selection", _prepare_selection_recommendation)
    graph.add_node("get_pricing", _get_pricing(engine))
    graph.add_node("respond", _respond_pricing)

    graph.add_edge(START, "prepare_selection")
    graph.add_edge("prepare_selection", "get_pricing")
    graph.add_edge("get_pricing", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


def build_quote_creation_graph(
    execution_engine: MCPExecutionEngine | None = None,
    llm_client: LLMClient | None = None,
):
    """Build a graph that prices selected products and creates a quote."""
    engine = execution_engine or MCPExecutionEngine(create_default_tool_registry())

    # Quote flow: frontend-approved selections are priced and persisted as a quote.
    graph = StateGraph(AgentState)
    graph.add_node("prepare_selection", _prepare_selection_recommendation)
    graph.add_node("get_pricing", _get_pricing(engine))
    graph.add_node("create_quote", _create_quote(engine))
    graph.add_node("respond", _respond_quote_creation(llm_client))

    graph.add_edge(START, "prepare_selection")
    graph.add_edge("prepare_selection", "get_pricing")
    graph.add_edge("get_pricing", "create_quote")
    graph.add_edge("create_quote", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


# ---------------------------------------------------------------------------
# State preparation nodes.
# These normalize frontend/backend input into the common state shape used by
# downstream pricing, quote, and response nodes.
# ---------------------------------------------------------------------------


def _analyze_intent(state: AgentState) -> AgentState:
    """Extract user intent and opportunity context into graph state."""
    user_input = _extract_user_input(state)
    sf_opportunity_id = _extract_sf_opportunity_id(state)
    logger.info(
        "Agent intent analyzed: intent=%s sf_opportunity_id=%s user_input_length=%s",
        "opportunity_to_quote",
        sf_opportunity_id,
        len(user_input),
    )
    return {
        "intent": "opportunity_to_quote",
        "sf_opportunity_id": sf_opportunity_id,
        "user_input": user_input,
        "status": "running",
    }


def _prepare_selection_recommendation(state: AgentState) -> AgentState:
    """Convert selected products into the recommendation shape expected by pricing."""
    sf_opportunity_id = _extract_sf_opportunity_id(state)
    # Deselected products stay in the UI but should not be sent to CPQ pricing.
    selected_products = [
        product
        for product in state.get("selected_products", [])
        if product.get("selected", True)
    ]
    logger.info(
        "Agent prepared selected products: sf_opportunity_id=%s product_count=%s",
        sf_opportunity_id,
        len(selected_products),
    )
    return {
        "intent": "quote_selection",
        "sf_opportunity_id": sf_opportunity_id,
        "selected_products": selected_products,
        # Pricing expects the same structure produced by the recommendation tool.
        "recommendation": {
            "sf_opportunity_id": sf_opportunity_id,
            "currency": state.get("currency", "USD"),
            "products": selected_products,
        },
        "persist_quote": state.get("persist_quote", False),
        "status": "running",
    }


# ---------------------------------------------------------------------------
# MCP tool nodes.
# These closures bind the execution engine once, then LangGraph calls the inner
# node with the current state during graph execution.
# ---------------------------------------------------------------------------


def _retrieve_context(engine: MCPExecutionEngine):
    """Create a graph node that retrieves RAG context when the prompt needs it."""

    def node(state: AgentState) -> AgentState:
        """Retrieve relevant RAG snippets or skip retrieval for non-domain prompts."""
        user_input = state.get("user_input", "")
        # RAG is intentionally conditional so generic commands do not require
        # embeddings, ChromaDB, or Ollama to be available.
        if not _should_retrieve_context(user_input):
            logger.info("Agent RAG skipped: reason=no_domain_keyword")
            return {"retrieved_context": []}

        logger.info("Agent requesting RAG context through MCP")
        # Agent -> MCP -> search_knowledge tool -> Retriever -> ChromaDB.
        result = engine.execute(
            "search_knowledge",
            {
                "query": user_input,
                "k": 3,
            },
        )
        retrieved_context = result.get("results", [])
        logger.info(
            "Agent RAG context retrieved: result_count=%s",
            len(retrieved_context),
        )
        return {"retrieved_context": retrieved_context}

    return node


def _get_opportunity(engine: MCPExecutionEngine):
    """Create a graph node that loads the opportunity through MCP."""

    def node(state: AgentState) -> AgentState:
        """Load the selected Salesforce opportunity into graph state."""
        logger.info(
            "Agent fetching opportunity through MCP: sf_opportunity_id=%s",
            state["sf_opportunity_id"],
        )
        opportunity = engine.execute(
            # Agent -> MCP -> get_opportunity tool -> Salesforce mock/data layer.
            "get_opportunity",
            {"sf_opportunity_id": state["sf_opportunity_id"]},
        )
        return {"opportunity": opportunity}

    return node


def _recommend_products(engine: MCPExecutionEngine):
    """Create a graph node that calls the CPQ recommendation tool."""

    def node(state: AgentState) -> AgentState:
        """Request CPQ product recommendations for the loaded opportunity."""
        logger.info("Agent requesting product recommendation through MCP")
        recommendation = engine.execute(
            # Agent -> MCP -> recommend_products tool -> CPQ recommendation rules.
            "recommend_products",
            {"opportunity": state["opportunity"]},
        )
        return {"recommendation": recommendation}

    return node


def _get_pricing(engine: MCPExecutionEngine):
    """Create a graph node that calls the CPQ pricing tool."""

    def node(state: AgentState) -> AgentState:
        """Price the current recommendation through the MCP pricing tool."""
        logger.info("Agent requesting pricing through MCP")
        pricing = engine.execute(
            # Agent -> MCP -> get_pricing tool -> CPQ pricing rules.
            "get_pricing",
            {"recommendation": state["recommendation"]},
        )
        return {"pricing": pricing}

    return node


def _create_quote(engine: MCPExecutionEngine):
    """Create a graph node that calls the CPQ quote creation tool."""

    def node(state: AgentState) -> AgentState:
        """Create a draft quote and keep tool outputs for trace rendering."""
        logger.info("Agent requesting quote creation through MCP")
        payload = {"pricing": state["pricing"]}
        if state.get("persist_quote"):
            # Persisting is enabled only for explicit quote creation flows.
            payload["persist"] = True

        # Agent -> MCP -> create_quote tool -> CPQ quote logic / SQLite.
        quote = engine.execute("create_quote", payload)
        return {
            "quote": quote,
            # The frontend architecture panel uses this grouped payload to show
            # what each layer produced.
            "tools_output": {
                "opportunity": state.get("opportunity", {}),
                "recommendation": state.get("recommendation", {}),
                "pricing": state["pricing"],
                "quote": quote,
            },
        }

    return node


# ---------------------------------------------------------------------------
# Response nodes and prompt builders.
# When an LLM client exists, prompts are sent to it. Otherwise deterministic
# fallback messages keep tests and local fallback mode stable.
# ---------------------------------------------------------------------------


def _respond(llm_client: LLMClient | None):
    """Create a graph node that builds the final full-flow assistant response."""

    def node(state: AgentState) -> AgentState:
        """Build the final response for the recommendation, pricing, and quote flow."""
        quote = state["quote"]
        recommendation = state["recommendation"]
        pricing = state["pricing"]
        assistant_message = _build_fallback_message(quote, pricing)
        logger.info(
            "Agent generating response: has_llm_client=%s context_count=%s product_count=%s",
            llm_client is not None,
            len(state.get("retrieved_context", [])),
            len(recommendation["products"]),
        )

        if llm_client is not None:
            # The LLM sees only curated business output and retrieved context,
            # not raw database rows or internal service objects.
            assistant_message = llm_client.chat(
                _build_response_prompt(
                    products=recommendation["products"],
                    pricing=pricing,
                    quote=quote,
                    user_input=state.get("user_input", ""),
                    retrieved_context=state.get("retrieved_context", []),
                )
            )

        final_answer = assistant_message.get("content", "")
        logger.info("Agent response completed: oracle_quote_id=%s", quote["oracle_quote_id"])
        return {
            "assistant_message": assistant_message,
            "final_answer": final_answer,
            "status": "completed",
            # `response` is shaped for FastAPI/Pydantic response models.
            "response": {
                "message": final_answer,
                "products": recommendation["products"],
                "pricing": pricing,
                "oracle_quote_id": quote["oracle_quote_id"],
            },
        }

    return node


def _respond_recommendation(llm_client: LLMClient | None):
    """Create a graph node that returns recommendation review output."""

    def node(state: AgentState) -> AgentState:
        """Build the review response before a quote is created."""
        recommendation = state["recommendation"]
        pricing = state["pricing"]
        assistant_message = _build_recommendation_fallback_message(recommendation, pricing)
        logger.info(
            "Agent recommendation ready: has_llm_client=%s context_count=%s product_count=%s",
            llm_client is not None,
            len(state.get("retrieved_context", [])),
            len(recommendation["products"]),
        )

        if llm_client is not None:
            # Recommendation prompts explicitly tell the model not to claim a
            # quote exists before the user reviews selections.
            assistant_message = llm_client.chat(
                _build_recommendation_prompt(
                    opportunity=state["opportunity"],
                    products=recommendation["products"],
                    pricing=pricing,
                    user_input=state.get("user_input", ""),
                    retrieved_context=state.get("retrieved_context", []),
                )
            )

        final_answer = assistant_message.get("content", "")
        run_steps = _build_run_steps(state, include_quote=False)
        return {
            "assistant_message": assistant_message,
            "final_answer": final_answer,
            "run_steps": run_steps,
            "status": "ready_for_review",
            "response": {
                "status": "ready_for_review",
                "message": final_answer,
                "opportunity": state["opportunity"],
                "products": recommendation["products"],
                "pricing": pricing,
                "retrieved_context": state.get("retrieved_context", []),
                "run_steps": run_steps,
            },
        }

    return node


def _respond_pricing(state: AgentState) -> AgentState:
    """Return pricing response state after selected products are priced."""
    run_steps = _build_run_steps(state, include_quote=False, include_recommendation=False)
    return {
        "run_steps": run_steps,
        "status": "priced",
        "response": {
            "status": "priced",
            "products": state["selected_products"],
            "pricing": state["pricing"],
            "run_steps": run_steps,
        },
    }


def _respond_quote_creation(llm_client: LLMClient | None):
    """Create a graph node that summarizes a newly created quote."""

    def node(state: AgentState) -> AgentState:
        """Build the final response after selected products become a quote."""
        quote = state["quote"]
        pricing = state["pricing"]
        assistant_message = _build_fallback_message(quote, pricing)
        logger.info(
            "Agent quote creation response: has_llm_client=%s product_count=%s",
            llm_client is not None,
            len(pricing.get("line_items", [])),
        )

        if llm_client is not None:
            assistant_message = llm_client.chat(
                _build_quote_creation_prompt(
                    pricing=pricing,
                    quote=quote,
                    selected_products=state.get("selected_products", []),
                )
            )

        final_answer = assistant_message.get("content", "")
        run_steps = _build_run_steps(state, include_quote=True, include_recommendation=False)
        return {
            "assistant_message": assistant_message,
            "final_answer": final_answer,
            "run_steps": run_steps,
            "status": "completed",
            "response": {
                "status": "completed",
                "message": final_answer,
                "quote": quote,
                "oracle_quote_id": quote["oracle_quote_id"],
                "products": state.get("selected_products", []),
                "pricing": pricing,
                "run_steps": run_steps,
            },
        }

    return node


def _build_response_prompt(
    products: list[dict],
    pricing: dict,
    quote: dict,
    user_input: str,
    retrieved_context: list[str] | None,
) -> list[dict]:
    """Build chat messages for the full quote creation response."""
    product_names = ", ".join(product["name"] for product in products)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a sales assistant. Use the provided context when relevant. "
                "If context is provided, use it and do not hallucinate outside it."
            ),
        }
    ]
    if retrieved_context:
        # Retrieved snippets are injected as system context so the assistant can
        # ground its explanation without inventing product or pricing facts.
        messages.append(
            {
                "role": "system",
                "content": "CONTEXT:\n" + "\n\n".join(retrieved_context),
            }
        )

    messages.append(
        {
            "role": "user",
            "content": (
                f"USER:\n{user_input}\n\n"
                f"Products: {product_names}. "
                f"Total: {pricing.get('currency', 'USD')} {pricing['total']}. "
                f"Quote ID: {quote['oracle_quote_id']}."
            ),
        }
    )
    return messages


def _build_recommendation_prompt(
    opportunity: dict,
    products: list[dict],
    pricing: dict,
    user_input: str,
    retrieved_context: list[str] | None,
) -> list[dict]:
    """Build chat messages that explain recommended products for review."""
    product_names = ", ".join(product["name"] for product in products)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a telecom infrastructure sales assistant. "
                "Use the provided context when relevant. "
                "Recommend products for sales rep review; do not claim the quote is created."
            ),
        }
    ]
    if retrieved_context:
        # This prompt is review-only; quote creation is a separate user action.
        messages.append(
            {
                "role": "system",
                "content": "CONTEXT:\n" + "\n\n".join(retrieved_context),
            }
        )

    messages.append(
        {
            "role": "user",
            "content": (
                f"USER:\n{user_input}\n\n"
                f"Opportunity: {opportunity.get('name')} for {opportunity.get('account', {}).get('name')}. "
                f"Recommended products: {product_names}. "
                f"Estimated total: {pricing.get('currency', 'USD')} {pricing['total']}. "
                "Ask the sales rep to review selections before creating the quote."
            ),
        }
    )
    return messages


def _build_quote_creation_prompt(
    pricing: dict,
    quote: dict,
    selected_products: list[dict],
) -> list[dict]:
    """Build chat messages that summarize a created draft quote."""
    product_names = ", ".join(product["name"] for product in selected_products)
    return [
        {
            "role": "system",
            "content": "You are a telecom infrastructure sales assistant.",
        },
        {
            "role": "user",
            "content": (
                f"Quote {quote['oracle_quote_id']} has been created for products: {product_names}. "
                f"Total: {pricing.get('currency', 'USD')} {pricing['total']}. "
                "Summarize the draft quote for the sales rep."
            ),
        },
    ]


def _build_recommendation_fallback_message(recommendation: dict, pricing: dict) -> dict:
    """Build a deterministic recommendation message when no LLM is configured."""
    return {
        "role": "assistant",
        "content": (
            f"Prepared {len(recommendation['products'])} recommended products "
            f"for sales review. Estimated total is "
            f"{pricing.get('currency', 'USD')} {pricing['total']}."
        ),
    }


def _build_fallback_message(quote: dict, pricing: dict) -> dict:
    """Build a deterministic quote creation message when no LLM is configured."""
    return {
        "role": "assistant",
        "content": (
            f"Created draft quote {quote['oracle_quote_id']} "
            f"for {pricing.get('currency', 'USD')} {pricing['total']}."
        ),
    }


def _build_run_steps(
    state: AgentState,
    include_quote: bool,
    include_recommendation: bool = True,
) -> list[dict[str, str]]:
    """Create UI trace steps from graph state and completed tool calls."""
    # These are user-facing trace rows, not the internal LangGraph execution log.
    steps: list[dict[str, str]] = []
    if include_recommendation:
        steps.extend(
            [
                {
                    "id": "analyze",
                    "label": "Analyze intent",
                    "layer": "Agent",
                    "status": "completed",
                    "detail": f"Opportunity {state.get('sf_opportunity_id', 'SF-OPP-001')} selected.",
                },
                {
                    "id": "retrieve_context",
                    "label": "Retrieve knowledge",
                    "layer": "MCP + RAG",
                    "status": "completed",
                    "detail": f"{len(state.get('retrieved_context', []))} context snippets returned.",
                },
                {
                    "id": "get_opportunity",
                    "label": "Fetch opportunity",
                    "layer": "MCP + Salesforce",
                    "status": "completed",
                    "detail": state.get("opportunity", {}).get("name", "Opportunity loaded."),
                },
                {
                    "id": "recommend_products",
                    "label": "Recommend products",
                    "layer": "MCP + CPQ",
                    "status": "completed",
                    "detail": f"{len(state.get('recommendation', {}).get('products', []))} products recommended.",
                },
            ]
        )

    steps.append(
        {
            "id": "get_pricing",
            "label": "Calculate pricing",
            "layer": "MCP + CPQ",
            "status": "completed",
            "detail": f"Total {state.get('pricing', {}).get('currency', 'USD')} {state.get('pricing', {}).get('total', 0)}.",
        }
    )

    if include_quote:
        steps.append(
            {
                "id": "create_quote",
                "label": "Create quote",
                "layer": "MCP + CPQ",
                "status": "completed",
                "detail": f"Draft quote {state.get('quote', {}).get('oracle_quote_id')} created.",
            }
        )

    return steps


def _extract_sf_opportunity_id(state: AgentState) -> str:
    """Extract the selected Salesforce opportunity id from graph state."""
    if state.get("sf_opportunity_id"):
        return state["sf_opportunity_id"]

    # Chat mode can infer an opportunity id if the user typed one into the prompt.
    for message in state.get("messages", []):
        content = str(message.get("content", ""))
        match = re.search(r"\bSF-OPP-\d+\b", content)
        if match:
            return match.group(0)

    # The demo defaults to the first seeded opportunity when no id is provided.
    return "SF-OPP-001"


def _extract_user_input(state: AgentState) -> str:
    """Extract the most recent user message from graph state."""
    if state.get("user_input"):
        return state["user_input"]

    messages = state.get("messages", [])
    if not messages:
        return ""

    return str(messages[-1].get("content", ""))


def _should_retrieve_context(user_input: str) -> bool:
    """Decide whether a prompt should trigger knowledge retrieval."""
    normalized = user_input.lower()
    # Keyword gating keeps RAG optional and predictable. This is deliberately
    # simple for the demo; a production system might use intent classification.
    knowledge_keywords = (
        "catalog",
        "pricing rule",
        "price rule",
        "sales playbook",
        "playbook",
        "discount",
        "enterprise support",
        "cpq handoff",
        "oracle cpq",
        "telecom",
        "netapp",
        "storage",
        "5g",
        "edge",
        "billing",
        "subscriber",
        "telemetry",
        "cdr",
        "archive",
        "hybrid cloud",
        "disaster recovery",
        "ontap",
        "storagegrid",
        "knowledge",
    )
    return any(keyword in normalized for keyword in knowledge_keywords)
