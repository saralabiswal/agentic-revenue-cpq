# TASKS.md

## Overview

Executable tasks for Enterprise AI Agent Platform.

Current status: all planned tasks 1-22 are implemented and validated.
Post-task UI and documentation enhancements are tracked below.

Latest validation:
- Python tests: `77 passed`
- Frontend build: `npm run build` passed after Architecture View update
- Docker build: `docker compose build backend frontend` passed
- Live Ollama backend `/chat` smoke test passed before the command-center expansion

---

## Phase 1: Bootstrap

### Task 1: Initialize Repo - Done

Created:
- `apps/`
- `services/`
- `integrations/`
- `schemas/`
- `configs/`
- `tests/`
- `docs/`

### Task 2: Backend Setup - Done

Implemented:
- FastAPI app
- `/health` endpoint
- `/chat` endpoint
- CORS for frontend access

### Task 3: Frontend Setup - Done

Implemented:
- Next.js app
- Live telecom quote command center
- Account selector
- Opportunity selector filtered by selected account
- Opportunity control panel
- Backend `/quote/recommendations`, `/quote/pricing`, and `/quote/create` integration
- Product selection and repricing
- Quote history and quote-version review
- Quote finalization and order placement
- Quote/product/pricing/explainability display
- Structured recommendation table with CPQ rule, category, billing model, quantity, term, and line-price details
- Business View / Architecture View mode switch
- Architecture trace console with layer badges, expandable payloads, layer contracts, and decision points
- Loading and error states

---

## Phase 2: LLM

### Task 4: LLMClient - Done

Implemented:
- Provider-neutral `LLMClient`
- `LLMMessage`
- `LLMResponse`

### Task 5: Ollama Client - Done

Implemented:
- `OllamaClient`
- `/api/chat` integration
- Configurable `OLLAMA_BASE_URL`
- Configurable `OLLAMA_MODEL`
- `create_llm_client` factory
- `LLM_PROVIDER=fallback` and `LLM_PROVIDER=ollama`

---

## Phase 3: MCP

### Task 6: Tool Registry - Done

Implemented:
- `ToolDefinition`
- `ToolRegistry`
- Registration and lookup
- Duplicate/missing tool validation

### Task 7: Execution Engine - Done

Implemented:
- `MCPExecutionEngine`
- Payload validation
- Result validation
- Tool error wrapping
- Execution logging

---

## Phase 4: Tools

### Task 8: Salesforce Mock - Done

Implemented:
- `get_opportunity()`
- `list_accounts()`
- `list_opportunities()`
- Mock account records
- Multiple mock opportunities per account

### Task 9: CPQ Recommendation - Done

Implemented:
- `recommend_products()`
- Product recommendation based on opportunity data
- NetApp-aligned mock product catalog for telecom data infrastructure
- CPQ rules for edge storage, block workloads, object archive/data lake, hybrid cloud, management, services, and support

### Task 10: Pricing - Done

Implemented:
- `get_pricing()`
- Quote line item pricing
- Subtotal, term discount, bundle discount, and total

### Task 11: Quote - Done

Implemented:
- `create_quote()`
- Draft quote id generation
- Persisted quote versions for app-created quotes
- Quote history
- Quote finalization
- Order placement after customer quote selection

### Task 12: MCP Wrappers - Done

Implemented MCP wrappers for:
- `list_accounts`
- `list_opportunities`
- `get_opportunity`
- `recommend_products`
- `get_pricing`
- `create_quote`
- `list_quotes`
- `finalize_quote`
- `list_orders`

---

## Phase 5: Agent

### Task 13: LangGraph Setup - Done

Implemented:
- LangGraph `StateGraph`
- Typed agent state

### Task 14: Flow Opportunity -> Quote - Done

Implemented flow:
START -> analyze -> retrieve_context -> get_opportunity -> recommend_products -> get_pricing -> create_quote -> respond -> END

### Task 15: LLM Integration - Done

Implemented:
- Agent receives optional `LLMClient`
- Prompt augmentation with retrieved context
- Fallback response when no LLM is configured
- Live Ollama response when `LLM_PROVIDER=ollama`

---

## Phase 6: API

### Task 16: Chat Endpoint - Done

Implemented:
- `POST /chat`
- `POST /quote/recommendations`
- `POST /quote/pricing`
- `POST /quote/create`
- Request schema
- Response schema
- Agent invocation
- Error handling

---

## Phase 7: Testing

### Task 17: Unit Tests - Done

Implemented tests for:
- LLM client abstraction
- Ollama client
- Tool registry
- MCP execution
- Salesforce mock
- CPQ recommendation/pricing/quote
- RAG components
- Logging

### Task 18: Integration Test - Done

Implemented:
- Opportunity-to-quote integration test
- Agent graph end-to-end test
- Backend `/chat` tests
- Architecture guardrail tests

---

## Phase 8: Deployment

### Task 19: Docker Compose - Done

Implemented:
- Backend container
- Frontend container
- Ollama container
- Chroma persistence volume
- Ollama data volume

### Task 20: End-to-End Run - Done

Validated:
- Backend `/health`
- Backend `/accounts`
- Backend `/opportunities`
- Backend `/chat`
- Backend `/quote/recommendations`
- Backend `/quote/pricing`
- Backend `/quote/create`
- Backend `/opportunities/{sf_opportunity_id}/quotes`
- Backend `/quote/finalize`
- Agent -> MCP -> RAG/tools -> LLM flow
- Frontend production build
- Docker image build
- Live Ollama smoke test

---

## Phase 9: Enhancements

### Task 21: RAG - Done

Implemented:
- `services/rag/embeddings.py`
- `services/rag/vector_store.py`
- `services/rag/retriever.py`
- `services/rag/ingest.py`
- `services/mcp/tools/rag_tools.py`
- ChromaDB persistent vector store
- Ollama embeddings with `nomic-embed-text`
- MCP tool `search_knowledge`
- Agentic RAG decision step

Architecture:
- Agent does not call RAG directly.
- Agent calls MCP `search_knowledge`.
- MCP handles RAG execution.

### Task 22: Logging - Done

Implemented:
- Central config in `configs/logging.py`
- Backend request lifecycle logs
- Agent stage logs
- MCP execution logs
- RAG ingestion/retrieval/vector-store logs
- Logging tests

---

## Post-Task Enhancements

### Enhancement A: Telecom Command Center UX - Done

Implemented:
- Business View as the primary sales rep workspace.
- Structured CPQ recommendation rows instead of raw assistant prose.
- Product include/exclude controls.
- Quantity and term edit controls.
- Live selected-product repricing.
- Pricing summary with subtotal, discounts, and total.
- Assistant summary moved to the explainability side panel.

Purpose:
- Make the app look and behave like a real quote review tool.
- Keep CPQ product data as the source of truth for recommendations.
- Keep LLM prose as supporting explanation, not the main product UI.

### Enhancement B: Architecture View - Done

Implemented:
- Business View / Architecture View switch.
- Architecture trace from sales rep command to quote creation.
- Architecture trace now extends through customer quote finalization and order placement.
- Layer badges for Human, Agent, MCP + RAG, MCP + Salesforce, MCP + CPQ, and LLMClient.
- Expandable trace details with input and output payloads.
- Layer contract panel explaining architecture ownership.
- Decision point panel for RAG trigger, CPQ rules, discounts, and human approval.
- Live trace status driven by the current recommendation, pricing, product selection, and quote state.

Purpose:
- Demonstrate the platform architecture end to end.
- Show that Agent orchestrates, MCP executes, RAG stays behind MCP, and LLMClient handles response generation.
- Give demo viewers a concrete explanation of each architecture step without leaving the app.

### Enhancement C: Account -> Opportunity -> Quotes -> Order Lifecycle - Done

Implemented:
- Multiple telecom accounts.
- Multiple opportunities under each account.
- Account and opportunity list endpoints.
- Quote history endpoint per opportunity.
- Persisted app-created quote versions in the mock CPQ lifecycle store.
- Quote finalization endpoint.
- Order placement from the finalized quote.
- Frontend account and opportunity selectors.
- Frontend quote-version panel.
- Frontend order summary.
- Architecture View steps for customer finalization and order placement.

Purpose:
- Move the app away from a static single-opportunity demo.
- Match the real business model where one account can own many opportunities, one opportunity can produce many quotes, and one customer-selected quote becomes an order.

---

## Phase 10: Live Data And First-Class Business Flow Plan

Status: implementation in progress. Completed items reflect the current local app.

### Task 23: External ID Naming Convention - Done

Goal:
- Make Salesforce and Oracle ownership clear in every API payload, DB table, frontend state object, test, and architecture trace.

Required key names:
- Salesforce Account: `sf_account_id`
- Salesforce Opportunity: `sf_opportunity_id`
- Oracle CPQ Quote: `oracle_quote_id`
- Oracle CPQ Order: `oracle_order_id`

Rules:
- Do not use generic external keys like `account_id`, `opportunity_id`, `quote_id`, or `order_id` in new API contracts.
- Local DB primary keys may use internal `id` columns, but external-system references must use the source-prefixed names.
- Agent state should carry source-prefixed IDs when referring to Salesforce or Oracle records.
- Frontend labels may display "Account", "Opportunity", "Quote", and "Order", but payload/state fields must remain source-prefixed.

Implementation checklist:
- [x] Update Salesforce mock/integration payloads to use `sf_account_id` and `sf_opportunity_id`.
- [x] Update Oracle CPQ quote/order payloads to use `oracle_quote_id` and `oracle_order_id`.
- [x] Update schemas and API responses.
- [x] Update frontend types and state.
- [x] Update tests and architecture guardrails for naming.
- [x] Preserve backward compatibility only if needed through temporary response aliases. No temporary aliases are currently used.

### Task 24: SQLite Persistence Layer - Done

Goal:
- Replace in-memory business lifecycle state with persistent local data.

Tables:
- [x] `accounts`
- [x] `opportunities`
- [x] `opportunity_requirements`
- [x] `products`
- [x] `pricing_rules`
- [x] `quotes`
- [x] `quote_line_items`
- [x] `orders`
- [x] `order_line_items`
- [x] `agent_runs`
- [x] `agent_run_steps`
- [x] `activity_events`

Key requirements:
- [x] Store Salesforce-owned IDs as `sf_account_id` and `sf_opportunity_id`.
- [x] Store Oracle-owned IDs as `oracle_quote_id` and `oracle_order_id`.
- [x] Keep local internal row IDs separate from external IDs.
- [x] Persist quote versions across backend restarts.
- [x] Persist finalized orders across backend restarts.
- [x] Persist activity timeline events.

### Task 25: Telecom Seed Dataset - Done

Goal:
- Make the app feel live by loading richer, varied demo data.

Seed data requirements:
- [x] 5 telecom accounts.
- [x] 2-3 opportunities per account.
- [x] Different opportunity stages: `Discovery`, `Proposal`, `Negotiation`, `Procurement`, `Closed Won`.
- [x] Different use cases: 5G edge, CDR archive, billing refresh, AI network analytics, hybrid cloud DR.
- [x] Existing quote history for several opportunities.
- [x] Existing accepted quotes and placed orders.
- [x] Activity timeline events.
- [x] Customer constraints such as budget, term preference, target close date, compliance need, incumbent vendor, and region.

### Task 26: Repository/Data Access Layer - Done

Goal:
- Keep business persistence behind repositories and preserve integration boundaries.

Implementation checklist:
- [x] Create database connection/config module.
- [x] Create schema initialization script.
- [x] Create seed script.
- [x] Create repository modules for accounts, opportunities, quotes, orders, runs, and activity.
- [x] Keep repositories out of the Agent layer.
- [x] Expose data access through MCP tools or backend read endpoints as appropriate.

### Task 27: API Expansion For Live App Data - Done

Goal:
- Support the complete Account -> Opportunity -> Quote -> Order app flow with persistent data.

Planned endpoints:
- [x] `GET /accounts`
- [x] `GET /accounts/{sf_account_id}/opportunities`
- [x] `GET /opportunities/{sf_opportunity_id}`
- [x] `GET /opportunities/{sf_opportunity_id}/quotes`
- [x] `GET /opportunities/{sf_opportunity_id}/activity`
- [x] `POST /quote/recommendations`
- [x] `POST /quote/pricing`
- [x] `POST /quote/create`
- [x] `POST /quote/finalize`
- [x] `GET /orders/{oracle_order_id}`
- [x] `GET /agent-runs`
- [x] `GET /agent-runs/{run_id}`

### Task 28: Activity Timeline And Run History - Done

Goal:
- Make each business action visible and persistent.

Implementation checklist:
- [x] Record activity when account/opportunity is viewed.
- [x] Record activity when recommendation is generated.
- [x] Record activity when product selection changes trigger pricing recalculation.
- [x] Record activity when pricing is recalculated.
- [x] Record activity when quote version is created.
- [x] Record activity when accepted quote creates an order.
- [x] Record activity when order is placed.
- [x] Persist Agent/MCP/RAG/CPQ run steps for Architecture View and run history APIs.

### Task 29: First-Class Command Execution - Partial

Goal:
- Allow typed commands to execute the same flow as UI buttons. Current implementation supports the recommendation command path; a full command parser for quote/order actions remains future work.

Example commands:
- `Show opportunities for Northstar Telecom`
- `Recommend products for sf opportunity SF-OPP-001`
- `Remove Cloud Volumes ONTAP and reprice`
- `Create a quote for the selected products`
- `Finalize Oracle quote ORA-Q-001-002`

Implementation checklist:
- [x] Add command bar for recommendation as the primary recommendation action.
- [ ] Add command parser or intent router.
- [x] Add session/current selection state.
- [x] Route recommendation command execution through Agent and MCP.
- [x] Require explicit user action for quote creation and order placement.
- [x] Update Business View from command results.
- [x] Update Architecture View from command run trace.

### Task 30: UI Refresh For Live Three-Cloud Story - Done

Goal:
- Make the app clearly show Salesforce CRM Cloud, Agentic Orchestration App, and Oracle CPQ Cloud as separate systems.

Implementation checklist:
- [x] Add top system ownership map.
- [x] Organize Business View into Salesforce lane, Agent lane, and Oracle CPQ lane.
- [x] Show sync/status badges for Salesforce reads and Oracle CPQ writes.
- [x] Add account/opportunity portfolio summary.
- [x] Add quote version comparison.
- [x] Add order summary.
- [x] Add activity timeline.
- [x] Keep Architecture View one click away.

### Task 31: Tests And Validation For Live Flow - Done

Goal:
- Protect the complete persistent business flow.

Validation checklist:
- [x] DB schema covered by repository/API tests.
- [x] Seed data covered by Salesforce/CPQ tests.
- [x] Repository behavior covered by Salesforce/CPQ lifecycle tests.
- [x] API tests for all new endpoints.
- [x] MCP tool tests for persistent quote/order lifecycle.
- [x] Agent graph tests for source-prefixed IDs.
- [x] Architecture guardrail tests for no direct integration calls from Agent.
- [x] Frontend build.
- [x] End-to-end smoke flow: Account -> Opportunity -> Recommendation -> Quote -> Finalize -> Order.

---

## Final Goal Status

Implemented:

Opportunity -> Product Recommendation -> Pricing -> Quote -> Context-aware Assistant Response

Primary app flow:

Account -> Opportunity -> AI Recommendation -> Sales Rep Selection -> Repricing -> Create Draft Quote Version -> Quote History -> Customer Finalization -> Order Placement -> Explainability

Architecture demo flow:

Sales Rep Command -> Agent Intent -> MCP.search_knowledge -> RAG Context -> MCP Salesforce Lookup -> MCP CPQ Recommendation -> MCP CPQ Pricing -> LLMClient Response -> Sales Rep Approval -> MCP CPQ Quote Creation -> Customer Quote Selection -> MCP CPQ Order Placement

Application surfaces:
- API: `http://127.0.0.1:8000`
- Frontend: `http://localhost:3000`
- Ollama: `http://localhost:11434`
