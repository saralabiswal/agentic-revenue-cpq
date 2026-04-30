# CODEX_PROJECT_PROMPT.md

You are a coding agent working inside this repository.

This project follows strict rules defined in:
- `FINAL_AGENTS.md` (primary architecture and guardrails)
- `TASKS.md` (completed execution plan and validation status)
- `PRD.md` (product context)

You MUST follow `FINAL_AGENTS.md` strictly.

---

## SOURCE OF TRUTH

1. `FINAL_AGENTS.md` -> architecture and rules
2. `TASKS.md` -> task completion and validation status
3. `PRD.md` -> product context

If there is a conflict:
-> Follow `FINAL_AGENTS.md`.

---

## PROJECT OVERVIEW

Enterprise AI Agent Platform for:

Salesforce Opportunity -> Oracle CPQ Quote automation

The project is now implemented as a local full-stack application with:
- FastAPI backend
- Next.js telecom quote command center frontend
- Business View for account/opportunity selection, sales rep product review, repricing, quote versions, and order placement
- Architecture View for explaining the live run across Human, Agent, MCP, RAG, Salesforce, CPQ, and LLMClient
- LangGraph agent
- MCP execution layer
- Salesforce/CPQ mock tools
- NetApp-aligned telecom infrastructure catalog and CPQ rules
- RAG knowledge retrieval through MCP
- Ollama chat and embeddings
- ChromaDB persistent vector store
- Centralized logging
- Docker Compose deployment

---

## ARCHITECTURE (STRICT)

You MUST enforce this separation:

- LLM = reasoning through `LLMClient`
- Agent = orchestration through LangGraph
- MCP = execution layer
- Tools = integrations
- RAG = knowledge service behind MCP

Strict flow:

User -> Frontend -> Backend -> Agent -> MCP -> Tools/RAG -> LLMClient -> Response

RAG flow:

User -> Agent -> MCP.search_knowledge -> Retriever -> ChromaDB -> Agent -> LLMClient

---

## NON-NEGOTIABLE RULES

You MUST:
- Route all tool calls through MCP.
- Use `LLMClient` for all LLM interactions.
- Keep modules isolated and modular.
- Keep RAG behind MCP.
- Keep integration access inside tool wrappers.
- Keep backend provider-neutral through the LLM factory.

You MUST NOT:
- Call APIs directly from agent.
- Bypass MCP.
- Call Ollama/vLLM directly from agent.
- Call Chroma directly from agent.
- Import integrations into agent.
- Mix responsibilities across layers.

If any rule is violated:
-> Stop and fix before continuing.

External ID naming is mandatory for the next live-data phase:
- Salesforce Account: `sf_account_id`
- Salesforce Opportunity: `sf_opportunity_id`
- Oracle CPQ Quote: `oracle_quote_id`
- Oracle CPQ Order: `oracle_order_id`

Do not add new generic external key names such as `account_id`, `opportunity_id`, `quote_id`, or `order_id`. Internal DB primary keys may use local `id` columns, but cross-system references and API payloads must use source-prefixed names.

---

## CURRENT IMPLEMENTATION MAP

Backend:
- `apps/backend/main.py`
- `/health`
- `/chat`
- `/accounts`
- `/opportunities`
- `/quote/recommendations`
- `/quote/pricing`
- `/quote/create`
- `/opportunities/{sf_opportunity_id}/quotes`
- `/opportunities/{sf_opportunity_id}/activity`
- `/quote/finalize`
- `/orders/{oracle_order_id}`
- `/agent-runs`
- `/agent-runs/{run_id}`
- CORS for frontend
- LLM factory usage

Frontend:
- `apps/frontend/app/page.tsx`
- Calls `/quote/recommendations`, `/quote/pricing`, and `/quote/create`
- Calls `/accounts`, `/opportunities`, `/opportunities/{sf_opportunity_id}/quotes`, `/opportunities/{sf_opportunity_id}/activity`, and `/quote/finalize`
- Business View with account/opportunity selectors, structured CPQ recommendation rows, selection controls, repricing, pricing summary, quote versions, and order placement
- Architecture View with live trace, layer badges, expandable input/output payloads, layer contracts, customer finalization, order placement, and decision points
- Supporting assistant summary and RAG evidence display

Agent:
- `services/agent/graph.py`
- LangGraph flow with `retrieve_context`
- Optional `LLMClient`

MCP:
- `services/mcp/registry.py`
- `services/mcp/engine.py`
- `services/mcp/tools/rag_tools.py`

Tools:
- `services/tools/opportunity_quote.py`
- `integrations/salesforce/`
- `integrations/cpq/`

LLM:
- `services/llm/client.py`
- `services/llm/ollama.py`
- `services/llm/factory.py`

RAG:
- `services/rag/embeddings.py`
- `services/rag/vector_store.py`
- `services/rag/retriever.py`
- `services/rag/ingest.py`

Logging:
- `configs/logging.py`

---

## TASK EXECUTION MODE

Tasks 1-22 are complete. Post-task UI enhancements are tracked in `TASKS.md`. Phase 10 now tracks the planned live-data and first-class business flow implementation. Mark Phase 10 checklist items done as implementation progresses.

For every new request:
1. Identify whether it is a bug fix, enhancement, validation, or docs update.
2. Read relevant code/docs first.
3. Create a short plan.
4. Implement minimal scoped changes.
5. Add or update tests when behavior changes.
6. Run relevant validation.
7. Validate architecture guardrails.

---

## VALIDATION RULES

Before completing any change:
- Ensure no direct API calls from agent.
- Ensure MCP is used for all tools.
- Ensure RAG is accessed only through MCP `search_knowledge`.
- Ensure LLM is accessed through `LLMClient`.
- Ensure backend remains provider-neutral.
- Ensure tests pass when applicable.
- Ensure logging remains present.

Latest known validation:
- Python tests: `77 passed`
- Frontend build: `npm run build` passed after Architecture View update
- Docker build: `docker compose build backend frontend` passed
- Live Ollama `/chat` smoke test passed before the command-center expansion

---

## CODING RULES

- Keep modules small and focused.
- Prefer existing patterns.
- Avoid over-engineering.
- Preserve strict layer boundaries.
- Keep tests deterministic by default.
- Use `LLM_PROVIDER=ollama` only for live local LLM runs.

---

## AGENT FLOW

1. Analyze intent and opportunity id.
2. Retrieve context through MCP `search_knowledge` when relevant.
3. Fetch opportunity through MCP.
4. Recommend products through MCP.
5. Calculate pricing through MCP.
6. Create quote through MCP.
7. Generate final response through `LLMClient` or fallback response.

---

## RUNTIME COMMANDS

Run Ollama:

```bash
ollama serve
```

Run backend with fallback response:

```bash
env UV_CACHE_DIR=.uv-cache uv run uvicorn apps.backend.main:app --host 127.0.0.1 --port 8000
```

Run backend with live Ollama:

```bash
LLM_PROVIDER=ollama OLLAMA_BASE_URL=http://localhost:11434 \
env UV_CACHE_DIR=.uv-cache uv run uvicorn apps.backend.main:app --host 127.0.0.1 --port 8000
```

Run frontend:

```bash
cd apps/frontend
npm run dev
```

Run tests:

```bash
env UV_CACHE_DIR=.uv-cache uv run --extra dev pytest -q
```

Run Docker:

```bash
docker compose up --build
```

---

## GOAL

Delivered:

Account -> Opportunity -> AI Recommendation -> Sales Rep Selection -> Repricing -> Quote Creation -> Customer Quote Finalization -> Order Placement -> Context-aware Assistant Response

Planned live-data goal:

Salesforce `sf_account_id` -> Salesforce `sf_opportunity_id` -> Agent/MCP/RAG run -> Oracle `oracle_quote_id` versions -> customer finalization -> Oracle `oracle_order_id`

Demo surface:

Business View -> Sales workflow  
Architecture View -> End-to-end platform explanation

---

## PRIORITY

Correct architecture > speed  
Validation > assumptions  
Modularity > completeness
