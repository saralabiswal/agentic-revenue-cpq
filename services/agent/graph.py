import logging
import re

from langgraph.graph import END, START, StateGraph

from services.agent.state import AgentState
from services.llm import LLMClient
from services.mcp import MCPExecutionEngine
from services.tools import create_default_tool_registry


logger = logging.getLogger(__name__)


def build_agent_graph(
    execution_engine: MCPExecutionEngine | None = None,
    llm_client: LLMClient | None = None,
):
    engine = execution_engine or MCPExecutionEngine(create_default_tool_registry())

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
    engine = execution_engine or MCPExecutionEngine(create_default_tool_registry())

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
    engine = execution_engine or MCPExecutionEngine(create_default_tool_registry())

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
    engine = execution_engine or MCPExecutionEngine(create_default_tool_registry())

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


def _analyze_intent(state: AgentState) -> AgentState:
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
    sf_opportunity_id = _extract_sf_opportunity_id(state)
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
        "recommendation": {
            "sf_opportunity_id": sf_opportunity_id,
            "currency": state.get("currency", "USD"),
            "products": selected_products,
        },
        "persist_quote": state.get("persist_quote", False),
        "status": "running",
    }


def _retrieve_context(engine: MCPExecutionEngine):
    def node(state: AgentState) -> AgentState:
        user_input = state.get("user_input", "")
        if not _should_retrieve_context(user_input):
            logger.info("Agent RAG skipped: reason=no_domain_keyword")
            return {"retrieved_context": []}

        logger.info("Agent requesting RAG context through MCP")
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
    def node(state: AgentState) -> AgentState:
        logger.info(
            "Agent fetching opportunity through MCP: sf_opportunity_id=%s",
            state["sf_opportunity_id"],
        )
        opportunity = engine.execute(
            "get_opportunity",
            {"sf_opportunity_id": state["sf_opportunity_id"]},
        )
        return {"opportunity": opportunity}

    return node


def _recommend_products(engine: MCPExecutionEngine):
    def node(state: AgentState) -> AgentState:
        logger.info("Agent requesting product recommendation through MCP")
        recommendation = engine.execute(
            "recommend_products",
            {"opportunity": state["opportunity"]},
        )
        return {"recommendation": recommendation}

    return node


def _get_pricing(engine: MCPExecutionEngine):
    def node(state: AgentState) -> AgentState:
        logger.info("Agent requesting pricing through MCP")
        pricing = engine.execute(
            "get_pricing",
            {"recommendation": state["recommendation"]},
        )
        return {"pricing": pricing}

    return node


def _create_quote(engine: MCPExecutionEngine):
    def node(state: AgentState) -> AgentState:
        logger.info("Agent requesting quote creation through MCP")
        payload = {"pricing": state["pricing"]}
        if state.get("persist_quote"):
            payload["persist"] = True

        quote = engine.execute("create_quote", payload)
        return {
            "quote": quote,
            "tools_output": {
                "opportunity": state.get("opportunity", {}),
                "recommendation": state.get("recommendation", {}),
                "pricing": state["pricing"],
                "quote": quote,
            },
        }

    return node


def _respond(llm_client: LLMClient | None):
    def node(state: AgentState) -> AgentState:
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
            "response": {
                "message": final_answer,
                "products": recommendation["products"],
                "pricing": pricing,
                "oracle_quote_id": quote["oracle_quote_id"],
            },
        }

    return node


def _respond_recommendation(llm_client: LLMClient | None):
    def node(state: AgentState) -> AgentState:
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
    def node(state: AgentState) -> AgentState:
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
    return {
        "role": "assistant",
        "content": (
            f"Prepared {len(recommendation['products'])} recommended products "
            f"for sales review. Estimated total is "
            f"{pricing.get('currency', 'USD')} {pricing['total']}."
        ),
    }


def _build_fallback_message(quote: dict, pricing: dict) -> dict:
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
    if state.get("sf_opportunity_id"):
        return state["sf_opportunity_id"]

    for message in state.get("messages", []):
        content = str(message.get("content", ""))
        match = re.search(r"\bSF-OPP-\d+\b", content)
        if match:
            return match.group(0)

    return "SF-OPP-001"


def _extract_user_input(state: AgentState) -> str:
    if state.get("user_input"):
        return state["user_input"]

    messages = state.get("messages", [])
    if not messages:
        return ""

    return str(messages[-1].get("content", ""))


def _should_retrieve_context(user_input: str) -> bool:
    normalized = user_input.lower()
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
