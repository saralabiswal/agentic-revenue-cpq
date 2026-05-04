"""FastAPI entry point exposing account, opportunity, quote, order, and agent run APIs.

Author: Sarala Biswal
"""

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from configs import configure_logging
from schemas import (
    AccountListResponse,
    ActivityListResponse,
    ChatRequest,
    ChatResponse,
    OpportunityListResponse,
    PricingRequest,
    PricingResponse,
    QuoteCreateRequest,
    QuoteCreateResponse,
    QuoteFinalizeRequest,
    QuoteFinalizeResponse,
    QuoteHistoryResponse,
    RecommendationRequest,
    RecommendationResponse,
    RuntimeProfileResponse,
)
from services.agent import create_agent_orchestrator
from services.data import (
    get_agent_run,
    get_order,
    list_agent_runs,
    record_activity,
    record_agent_run,
)
from services.llm import create_llm_client
from services.mcp.factory import create_default_mcp_engine
from services.platform import get_runtime_profile_payload


# Backend request flow:
# 1. The Next.js frontend calls these FastAPI routes.
# 2. Simple read routes execute named MCP tools directly.
# 3. Agentic routes build state and invoke an AgentOrchestrator workflow.
# 4. AgentOrchestrator calls MCP tools for Salesforce, CPQ, RAG, and data actions.
# 5. The backend records audit/activity details and returns typed API responses.
configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title="Enterprise AI Agent Platform")

# Allow the local Next.js app to call the API during development. Production
# deployments can replace this with FRONTEND_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health and Salesforce-style read APIs.
# These routes are thin API adapters. They do not know how Salesforce works;
# they call MCP tools, and the tool layer routes to the mock CRM/data layer.
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight backend health response."""
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/runtime/profile", response_model=RuntimeProfileResponse)
def runtime_profile() -> RuntimeProfileResponse:
    """Return read-only runtime provider profile metadata for UI display."""
    logger.info("Runtime profile requested")
    # This endpoint is intentionally informational. Provider selection stays in
    # backend deployment config and this response never includes secrets or URLs.
    return RuntimeProfileResponse(**get_runtime_profile_payload())


@app.get("/accounts", response_model=AccountListResponse)
def list_account_records() -> AccountListResponse:
    """Return account records for the frontend account selector."""
    logger.info("Account list requested")
    # Backend -> MCP tool -> Salesforce mock/data repository.
    result = _execute_mcp_tool("list_accounts", {})
    return AccountListResponse(accounts=result["accounts"])


@app.get("/opportunities", response_model=OpportunityListResponse)
def list_opportunity_records(sf_account_id: str | None = None) -> OpportunityListResponse:
    """Return opportunities, optionally scoped to one account."""
    logger.info("Opportunity list requested: sf_account_id=%s", sf_account_id)
    payload = {"sf_account_id": sf_account_id} if sf_account_id else {}
    # Optional account filtering is passed through as MCP payload data.
    result = _execute_mcp_tool("list_opportunities", payload)
    return OpportunityListResponse(opportunities=result["opportunities"])


@app.get(
    "/accounts/{sf_account_id}/opportunities",
    response_model=OpportunityListResponse,
)
def list_account_opportunity_records(sf_account_id: str) -> OpportunityListResponse:
    """Return opportunities for one account and record the portfolio view."""
    logger.info("Account opportunity list requested: sf_account_id=%s", sf_account_id)
    # Activity records power the timeline shown in the frontend.
    record_activity(
        sf_account_id=sf_account_id,
        system="Salesforce CRM Cloud",
        event_type="account_viewed",
        title="Account portfolio viewed",
        detail=f"Salesforce account {sf_account_id} opportunities loaded.",
    )
    result = _execute_mcp_tool("list_opportunities", {"sf_account_id": sf_account_id})
    return OpportunityListResponse(opportunities=result["opportunities"])


@app.get("/opportunities/{sf_opportunity_id}")
def get_opportunity_record(sf_opportunity_id: str) -> dict:
    """Return one opportunity and record that it was viewed."""
    logger.info("Opportunity detail requested: sf_opportunity_id=%s", sf_opportunity_id)
    # The backend fetches the CRM object first, then records the view event.
    opportunity = _execute_mcp_tool(
        "get_opportunity",
        {"sf_opportunity_id": sf_opportunity_id},
    )
    record_activity(
        sf_opportunity_id=sf_opportunity_id,
        system="Salesforce CRM Cloud",
        event_type="opportunity_viewed",
        title="Opportunity viewed",
        detail=f"Salesforce opportunity {sf_opportunity_id} details loaded.",
    )
    return opportunity


# ---------------------------------------------------------------------------
# Opportunity detail side panels.
# Quote history and activity are read through MCP so the frontend can reload
# current state after pricing, quote creation, or order placement.
# ---------------------------------------------------------------------------


@app.get(
    "/opportunities/{sf_opportunity_id}/quotes",
    response_model=QuoteHistoryResponse,
)
def list_quote_records(sf_opportunity_id: str) -> QuoteHistoryResponse:
    """Return quote versions for an opportunity."""
    logger.info("Quote history requested: sf_opportunity_id=%s", sf_opportunity_id)
    result = _execute_mcp_tool("list_quotes", {"sf_opportunity_id": sf_opportunity_id})
    return QuoteHistoryResponse(
        sf_opportunity_id=sf_opportunity_id,
        quotes=result["quotes"],
    )


@app.get(
    "/opportunities/{sf_opportunity_id}/activity",
    response_model=ActivityListResponse,
)
def list_activity_records(sf_opportunity_id: str) -> ActivityListResponse:
    """Return activity timeline events for an opportunity."""
    logger.info("Activity requested: sf_opportunity_id=%s", sf_opportunity_id)
    result = _execute_mcp_tool(
        "list_activity",
        {"sf_opportunity_id": sf_opportunity_id},
    )
    return ActivityListResponse(
        sf_opportunity_id=sf_opportunity_id,
        activity=result["activity"],
    )


# ---------------------------------------------------------------------------
# Agentic opportunity-to-quote APIs.
# These routes build the initial agent state. The orchestrator then owns the ordered
# workflow: analyze input, retrieve context, call tools, and build responses.
# ---------------------------------------------------------------------------


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Run the full chat-driven opportunity-to-quote workflow."""
    logger.info(
        "Chat request received: has_sf_opportunity_id=%s message_length=%s",
        bool(request.sf_opportunity_id),
        len(request.message),
    )
    state = {
        "messages": [
            {
                "role": "user",
                "content": request.message,
            }
        ]
    }
    if request.sf_opportunity_id:
        # Supplying this id anchors the agent workflow to a selected opportunity.
        state["sf_opportunity_id"] = request.sf_opportunity_id

    try:
        # Full workflow: opportunity -> recommendation -> pricing -> quote -> response.
        result = create_agent_orchestrator(
            llm_client=create_llm_client(),
        ).run_chat(state)
    except Exception as exc:
        logger.exception(
            "Chat request failed: has_sf_opportunity_id=%s",
            bool(request.sf_opportunity_id),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = result["response"]
    logger.info(
        "Chat request completed: status=%s oracle_quote_id=%s product_count=%s",
        result["status"],
        response["oracle_quote_id"],
        len(response["products"]),
    )
    return ChatResponse(
        status=result["status"],
        message=response["message"],
        oracle_quote_id=response["oracle_quote_id"],
        products=response["products"],
        pricing=response["pricing"],
    )


@app.post("/quote/recommendations", response_model=RecommendationResponse)
def recommend_quote(request: RecommendationRequest) -> RecommendationResponse:
    """Recommend products and pricing without creating a quote."""
    logger.info(
        "Recommendation request received: sf_opportunity_id=%s message_length=%s",
        request.sf_opportunity_id,
        len(request.message),
    )
    state = {
        "sf_opportunity_id": request.sf_opportunity_id,
        "messages": [
            {
                "role": "user",
                "content": request.message,
            }
        ],
    }

    try:
        # Recommendation workflow stops before quote creation so the user can review products.
        result = create_agent_orchestrator(
            llm_client=create_llm_client(),
        ).run_recommendation(state)
    except Exception as exc:
        logger.exception(
            "Recommendation request failed: sf_opportunity_id=%s",
            request.sf_opportunity_id,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = result["response"]
    # Agent runs are stored separately from business activity so the UI can show
    # explainability and execution history for agent decisions.
    record_agent_run(
        sf_opportunity_id=request.sf_opportunity_id,
        intent="recommendation",
        status=response["status"],
        steps=response["run_steps"],
    )
    logger.info(
        "Recommendation request completed: sf_opportunity_id=%s product_count=%s total=%s",
        request.sf_opportunity_id,
        len(response["products"]),
        response["pricing"]["total"],
    )
    return RecommendationResponse(**response)


@app.post("/quote/pricing", response_model=PricingResponse)
def price_quote(request: PricingRequest) -> PricingResponse:
    """Reprice the currently selected products."""
    logger.info(
        "Pricing request received: sf_opportunity_id=%s product_count=%s",
        request.sf_opportunity_id,
        len(request.products),
    )
    state = {
        "sf_opportunity_id": request.sf_opportunity_id,
        "currency": request.currency,
        # Pydantic models are converted into plain dictionaries because agent
        # nodes and MCP tools pass JSON-like state between layers.
        "selected_products": [product.model_dump() for product in request.products],
    }

    try:
        # Pricing workflow reuses the same CPQ pricing tool without recommendation.
        result = create_agent_orchestrator().run_pricing(state)
    except Exception as exc:
        logger.exception(
            "Pricing request failed: sf_opportunity_id=%s",
            request.sf_opportunity_id,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = result["response"]
    # Record both business activity and agent run history: activity explains the
    # deal timeline, while run history explains agent/tool execution.
    record_activity(
        sf_opportunity_id=request.sf_opportunity_id,
        system="Oracle CPQ Cloud",
        event_type="pricing_recalculated",
        title="Pricing recalculated",
        detail=(
            f"Oracle CPQ repriced {len(response['pricing']['line_items'])} "
            f"selected products at {response['pricing']['currency']} {response['pricing']['total']}."
        ),
    )
    record_agent_run(
        sf_opportunity_id=request.sf_opportunity_id,
        intent="pricing",
        status=response["status"],
        steps=response["run_steps"],
    )
    logger.info(
        "Pricing request completed: sf_opportunity_id=%s total=%s",
        request.sf_opportunity_id,
        response["pricing"]["total"],
    )
    return PricingResponse(**response)


@app.post("/quote/create", response_model=QuoteCreateResponse)
def create_quote_from_selection(request: QuoteCreateRequest) -> QuoteCreateResponse:
    """Create a persisted quote from reviewed product selections."""
    logger.info(
        "Quote creation request received: sf_opportunity_id=%s product_count=%s",
        request.sf_opportunity_id,
        len(request.products),
    )
    state = {
        "sf_opportunity_id": request.sf_opportunity_id,
        "currency": request.currency,
        "selected_products": [product.model_dump() for product in request.products],
        # This flag tells the quote workflow to persist the CPQ quote in SQLite
        # instead of returning only a transient draft response.
        "persist_quote": True,
    }

    try:
        # Quote creation workflow: selected products -> pricing -> create quote -> response.
        result = create_agent_orchestrator(
            llm_client=create_llm_client(),
        ).run_quote_creation(state)
    except Exception as exc:
        logger.exception(
            "Quote creation request failed: sf_opportunity_id=%s",
            request.sf_opportunity_id,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = result["response"]
    record_agent_run(
        sf_opportunity_id=request.sf_opportunity_id,
        intent="quote_creation",
        status=response["status"],
        steps=response["run_steps"],
    )
    logger.info(
        "Quote creation request completed: sf_opportunity_id=%s oracle_quote_id=%s total=%s",
        request.sf_opportunity_id,
        response["oracle_quote_id"],
        response["pricing"]["total"],
    )
    return QuoteCreateResponse(**response)


# ---------------------------------------------------------------------------
# Quote finalization and order APIs.
# Finalization is not an LLM task: the backend asks MCP to run the CPQ lifecycle
# tool, which accepts the quote, supersedes older drafts, and creates an order.
# ---------------------------------------------------------------------------


@app.post("/quote/finalize", response_model=QuoteFinalizeResponse)
def finalize_quote_from_selection(request: QuoteFinalizeRequest) -> QuoteFinalizeResponse:
    """Accept a quote and place the matching order."""
    logger.info("Quote finalization requested: oracle_quote_id=%s", request.oracle_quote_id)
    try:
        result = _execute_mcp_tool(
            "finalize_quote",
            {"oracle_quote_id": request.oracle_quote_id},
        )
    except Exception as exc:
        logger.exception(
            "Quote finalization failed: oracle_quote_id=%s",
            request.oracle_quote_id,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info(
        "Quote finalization completed: oracle_quote_id=%s oracle_order_id=%s",
        result["quote"]["oracle_quote_id"],
        result["order"]["oracle_order_id"],
    )
    return QuoteFinalizeResponse(status="order_placed", **result)


@app.get("/orders/{oracle_order_id}")
def get_order_record(oracle_order_id: str) -> dict:
    """Return one placed order by Oracle order id."""
    logger.info("Order detail requested: oracle_order_id=%s", oracle_order_id)
    order = get_order(oracle_order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order not found: {oracle_order_id}")

    return order


# ---------------------------------------------------------------------------
# Agent audit APIs.
# These routes expose stored agent run history so the frontend can show what the
# agent did after recommendation, pricing, and quote-creation actions.
# ---------------------------------------------------------------------------


@app.get("/agent-runs")
def list_agent_run_records(
    sf_opportunity_id: str | None = None,
    limit: int = 20,
) -> dict:
    """Return recent agent run audit records."""
    logger.info(
        "Agent run history requested: sf_opportunity_id=%s limit=%s",
        sf_opportunity_id,
        limit,
    )
    return {
        "runs": list_agent_runs(
            sf_opportunity_id=sf_opportunity_id,
            limit=limit,
        )
    }


@app.get("/agent-runs/{run_id}")
def get_agent_run_record(run_id: str) -> dict:
    """Return one detailed agent run audit record."""
    logger.info("Agent run detail requested: run_id=%s", run_id)
    run = get_agent_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Agent run not found: {run_id}")

    return run


def _execute_mcp_tool(tool_name: str, payload: dict) -> dict:
    """Execute one MCP tool and translate failures into HTTP errors."""
    # Create a fresh default engine per route call. The factory wires the MCP
    # registry with Salesforce, CPQ, activity, quote, order, and RAG tools.
    engine = create_default_mcp_engine()
    try:
        # MCP failures become HTTP 400 responses so frontend callers receive a
        # clear API error instead of a raw Python exception.
        return engine.execute(tool_name, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
