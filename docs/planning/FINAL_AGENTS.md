# AGENTS.md

## 1. Project Overview

Enterprise AI Agent Platform enabling:
- Salesforce Opportunity -> Oracle CPQ Quote automation
- Enterprise AI Agentic Workflow revenue-flow platform
- Account -> Opportunities -> Quotes -> Order lifecycle
- NetApp-aligned mock catalog, pricing, and support/service bundles
- MCP-based tool orchestration
- LangGraph agent reasoning
- RAG-backed knowledge retrieval exposed only through MCP
- LLM abstraction with Ollama in phase 1 and vLLM as a future provider path
- FastAPI backend and Next.js frontend with Business, Architecture, and Developer views

Implemented core flow:
User -> Frontend -> Backend -> Agent -> MCP -> Tools/RAG -> LLMClient -> Response

RAG flow:
User -> Agent -> MCP.search_knowledge -> RAG Retriever -> ChromaDB -> Results -> Agent -> LLMClient

---

## 2. Tech Stack

Backend:
- Python 3.11+
- FastAPI
- LangGraph
- Standard Python logging
- ChromaDB persistent local vector store

Frontend:
- Next.js
- React app with Business View, Architecture View, and Developer View
- Business View: compact Salesforce read context, command picker, recommended products, selected-product repricing, quote versions, order placement, collapsed Agent Workbench, and collapsed Activity Timeline
- Architecture View: live layer trace collapsed by default, expandable payloads, layer contracts, and run evidence
- Developer View: setup/runtime grouped code-flow diagrams for implementation teaching

LLM:
- Ollama chat model: `llama3.1`
- Ollama embedding model: `nomic-embed-text`
- vLLM is a future provider target behind `LLMClient`

Data and deployment:
- Docker Compose
- Local Chroma persistence at `./chroma_db`
- Docker volumes for Chroma and Ollama data
- Local SQLite persistence for business lifecycle data in `app_data/business.sqlite3`

---

## 3. Architecture Rules (MANDATORY)

Separation:
- LLM = reasoning through `LLMClient`
- Agent = orchestration through LangGraph
- MCP = execution layer
- Tools = integrations and knowledge access
- RAG = knowledge service behind MCP

DO:
- Route ALL tool calls through MCP
- Use `LLMClient` for all LLM interactions
- Keep modules isolated
- Expose RAG only through `search_knowledge`
- Keep direct integration calls inside tool wrappers
- Keep direct Chroma/Ollama embedding calls inside RAG services

DO NOT:
- Call APIs directly from agent
- Bypass MCP
- Call Ollama/vLLM directly from agent
- Call Chroma directly from agent
- Mix responsibilities across layers

External ID naming:
- Salesforce-owned Account IDs must be named `sf_account_id`.
- Salesforce-owned Opportunity IDs must be named `sf_opportunity_id`.
- Oracle CPQ-owned Quote IDs must be named `oracle_quote_id`.
- Oracle CPQ-owned Order IDs must be named `oracle_order_id`.
- Do not introduce new generic external key names such as `account_id`, `opportunity_id`, `quote_id`, or `order_id`.
- Local database primary keys may use internal `id` fields, but cross-system links must use source-prefixed names.

---

## 4. Repository Structure

apps/
  backend/
  frontend/

configs/
  logging.py

services/
  agent/
  llm/
  mcp/
    tools/
  rag/
  tools/

integrations/
  cpq/
  salesforce/

schemas/
tests/
docs/

---

## 5. Runtime Configuration

Backend:
- `LLM_PROVIDER=fallback` keeps deterministic fallback responses.
- `LLM_PROVIDER=ollama` enables live Ollama chat through `OllamaClient`.
- `OLLAMA_BASE_URL` defaults to `http://localhost:11434`.
- `OLLAMA_MODEL` defaults to `llama3.1`.
- `LOG_LEVEL` defaults to `INFO`.
- `FRONTEND_ORIGINS` defaults to `http://localhost:3000,http://127.0.0.1:3000`.

RAG:
- Embeddings use Ollama `/api/embeddings`.
- Embedding model is `nomic-embed-text`.
- Vector store is persistent ChromaDB.
- Collection name is `knowledge`.

---

## 6. Commands

Run Ollama:

```bash
ollama serve
```

Ingest sample RAG documents:

```bash
env UV_CACHE_DIR=.uv-cache uv run python -m services.rag.ingest
```

Run backend with deterministic fallback response:

```bash
env UV_CACHE_DIR=.uv-cache uv run uvicorn apps.backend.main:app --host 127.0.0.1 --port 8000
```

Run backend with live Ollama LLM:

```bash
LLM_PROVIDER=ollama OLLAMA_BASE_URL=http://localhost:11434 \
env UV_CACHE_DIR=.uv-cache uv run uvicorn apps.backend.main:app --host 127.0.0.1 --port 8000
```

Run frontend:

```bash
cd apps/frontend
npm run dev
```

Run frontend production build/server:

```bash
cd apps/frontend
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run build
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run start -- --hostname 127.0.0.1 --port 3000
```

Docker:

```bash
docker compose up --build
```

---

## 7. MCP Rules

- MCP is the execution layer.
- All tools are registered in `ToolRegistry`.
- `MCPExecutionEngine` validates payloads/results and logs every call.
- Registered tools:
  - `list_accounts`
  - `list_opportunities`
  - `get_opportunity`
  - `recommend_products`
  - `get_pricing`
  - `create_quote`
  - `list_quotes`
  - `finalize_quote`
  - `list_orders`
  - `list_activity`
  - `search_knowledge`
- `search_knowledge` is the only entry point to RAG.

---

## 8. LLM Interface

```python
class LLMClient:
    def chat(self, messages: list[dict]) -> dict:
        pass
```

Implemented:
- `services.llm.client.LLMClient`
- `services.llm.ollama.OllamaClient`
- `services.llm.factory.create_llm_client`

The backend uses the factory. The agent receives an optional `LLMClient` and never imports provider clients directly.

---

## 9. Agent Flow

Implemented LangGraph recommendation flow:

START
 -> analyze
 -> retrieve_context
 -> get_opportunity
 -> recommend_products
 -> get_pricing
 -> respond
END

Human-in-the-loop command-center flows:
- Recommendation graph: analyze -> retrieve_context -> get_opportunity -> recommend_products -> get_pricing -> respond
- Pricing graph: prepare_selection -> get_pricing -> respond
- Quote graph: prepare_selection -> get_pricing -> create_quote -> respond

Agent behavior:
- Extracts or defaults opportunity id.
- Decides whether the user query needs domain knowledge.
- Calls MCP `search_knowledge` only when domain knowledge is useful.
- Calls Salesforce/CPQ tools through MCP.
- Builds an LLM prompt with retrieved context when present.
- Uses deterministic fallback response when no `LLMClient` is configured.

---

## 10. Frontend Flow

The Next.js command center:
- Loads accounts and opportunities.
- Lets the user select an account and then an opportunity.
- Accepts a sales command for the selected opportunity.
- Calls backend `/quote/recommendations`.
- Lets the sales rep include/exclude recommended products.
- Lets the sales rep adjust quantity and term.
- Calls backend `/quote/pricing` to refresh selected-product pricing.
- Calls backend `/quote/create` only after sales rep approval.
- Calls backend `/opportunities/{sf_opportunity_id}/quotes` to show quote versions.
- Calls backend `/opportunities/{sf_opportunity_id}/activity` to show the activity timeline.
- Calls backend `/quote/finalize` to finalize a selected quote and place an order.
- Calls backend `/orders/{oracle_order_id}` and `/agent-runs` endpoints for order detail and run history when needed.
- Shows loading and error states.
- Renders account, opportunity, quote id, order id, total, structured product lines, discounts, quote versions, RAG context, assistant summary, and agent run steps.
- Provides Business View for the sales workflow.
- Provides Architecture View for explaining the live run across Human, Agent, MCP, RAG, Salesforce, CPQ, LLMClient, customer finalization, and order placement.
- Shows collapsed-by-default Architecture View payloads for inputs and outputs, using frontend state returned by the backend.
- Provides Developer View for setup/runtime implementation code-flow diagrams.
- Uses a command picker plus command details field; Enter runs the command and Shift+Enter inserts a new line.
- Uses `NEXT_PUBLIC_API_BASE_URL`, defaulting to `http://localhost:8000`.

Frontend rules:
- Architecture View is explanatory only; it must not bypass backend, agent, MCP, RAG, or tool boundaries.
- Product recommendations should render from structured CPQ response data, not from raw LLM prose.
- LLM-generated sales text should be supporting explanation, not the source of product selection state.
- The UI may label records as Account, Opportunity, Quote, and Order, but code and payloads should keep `sf_` and `oracle_` source-owned key names.

---

## 10.1 Implemented Live Data Flow

The app feels live through persistent local data.

Implemented flow:

```text
Salesforce Account sf_account_id
 -> Salesforce Opportunity sf_opportunity_id
 -> Agentic recommendation and pricing run
 -> Oracle CPQ Quote oracle_quote_id
 -> Customer finalization
 -> Oracle CPQ Order oracle_order_id
```

Implemented persistence:
- SQLite for business lifecycle state.
- ChromaDB remains the vector store for RAG.
- Agent run history and activity events are persisted.
- Quote and order lifecycle survives backend restarts.

Implemented UI story:
- Salesforce CRM Cloud lane owns Accounts and Opportunities.
- Agentic Orchestration App lane owns commands, reasoning, MCP execution, RAG evidence, and recommendations.
- Oracle CPQ Cloud lane owns Quotes, Quote Lines, Orders, and Order Lines.
- Developer View owns code-path teaching for setup and runtime boundaries.

---

## 11. Logging

Central logging is configured in `configs/logging.py`.

Logged surfaces:
- Backend health and chat lifecycle.
- Agent intent, RAG decision, tool stages, and response generation.
- MCP tool execution, failures, payload keys, and result keys.
- RAG ingestion, retrieval, embeddings, and vector-store activity.

Logs should include operational metadata and counts, not full sensitive payloads.

---

## 12. Testing And Validation

Current validation:
- Python tests: `78 passed`
- Frontend production build: `npm run build` passed after Business/Architecture/Developer View update
- Docker image build: `docker compose build backend frontend` passed
- Live Ollama `/chat` smoke test passed before the command-center expansion

Test categories:
- Backend API tests
- LLM abstraction and Ollama client tests
- MCP registry and execution tests
- Salesforce/CPQ mock integration tests
- Agent graph tests
- RAG tests
- Logging tests
- Architecture guardrail tests

---

## 13. Guardrails

Before completing changes:
- No direct API calls from agent
- MCP used for all tool calls
- RAG accessed only through MCP `search_knowledge`
- LLM accessed through `LLMClient`
- Backend remains provider-neutral through LLM factory
- Tests pass
- Logging remains present

---

## FINAL PRINCIPLE

LLM = reasoning  
Agent = orchestration  
MCP = execution  
RAG = knowledge service behind MCP
