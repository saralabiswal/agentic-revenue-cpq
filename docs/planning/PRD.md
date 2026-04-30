# Product Requirements Document (PRD)
## Enterprise AI Agent Platform - Telecom Quote Command Center

---

## 1. Objective

Build a standalone AI agent platform that automates Salesforce Opportunity -> Oracle CPQ Quote workflows using:
- LangGraph for agent orchestration
- MCP for all execution/tool access
- `LLMClient` for provider-neutral reasoning
- RAG for context-aware telecom infrastructure sales knowledge
- FastAPI and Next.js for a usable local application

---

## 2. Problem Statement

Telecom infrastructure sales workflows are fragmented across CRM, CPQ, product catalog knowledge, pricing rules, quote versions, order handoff, and sales playbooks. This creates manual effort and inconsistent quote preparation. The platform provides an agentic workflow that starts from Account and Opportunity context, recommends NetApp-aligned storage and data infrastructure products, prices selected products, explains every step, creates multiple draft quote versions, and places an order after the customer finalizes a quote.

---

## 3. Target Users

- Sales representatives
- Sales operations
- Platform engineers
- AI/automation engineers validating enterprise agent architecture

---

## 4. MVP Scope

### Included

- Live command center in Next.js
- FastAPI backend with `/health`, `/chat`, `/quote/recommendations`, `/quote/pricing`, and `/quote/create`
- Account, opportunity, quote-history, and quote-finalization APIs
- LangGraph agent flow
- MCP registry and execution engine
- Salesforce mock account and opportunity lookup
- Oracle CPQ mock recommendation, pricing, selected-product repricing, quote creation, quote history, finalization, and order placement
- NetApp-aligned mock product catalog for telecom infrastructure
- RAG knowledge layer for product catalog, pricing rules, and sales playbooks
- Structured sales rep product review with include/exclude, quantity, term, and line-price controls
- Architecture View that explains the live run across Human, Agent, MCP, RAG, Salesforce, CPQ, and LLMClient layers
- ChromaDB persistent local vector store
- Ollama chat and embedding support
- Deterministic fallback response mode
- Centralized logging
- Docker Compose deployment
- Unit, integration, RAG, logging, and guardrail tests

### Excluded

- RBAC
- Multi-tenant data isolation
- Real Salesforce and Oracle CPQ credentials
- Kubernetes/OCI deployment
- Production observability stack
- vLLM runtime integration

---

## 5. Architecture

Layer ownership:
- LLM = reasoning through `LLMClient`
- Agent = orchestration through LangGraph
- MCP = execution layer
- Tools = integration wrappers
- RAG = knowledge service behind MCP

Primary flow:
User -> Frontend -> Backend -> Agent -> MCP -> Tools -> LLMClient -> Response

Command-center flow:
User -> Frontend -> Account -> Opportunity -> Backend -> Agent -> MCP recommendation/pricing -> Sales rep selection -> Agent -> MCP quote creation -> Quote history -> Customer finalization -> MCP order placement -> Response

RAG flow:
User -> Agent -> MCP.search_knowledge -> Retriever -> ChromaDB -> Context -> Agent -> LLMClient

Architecture explanation flow:
Business run data -> Frontend Architecture View -> Layer trace -> Expandable input/output payloads -> Layer contracts and decision points

The agent does not call integrations, Chroma, Ollama, or RAG directly.

---

## 6. Key Decisions

- LangGraph is used for explicit agent state transitions.
- MCP is the only execution boundary for tools.
- RAG is exposed as the MCP tool `search_knowledge`.
- Ollama is used for phase 1 chat and embeddings.
- `LLM_PROVIDER=fallback` keeps tests deterministic.
- `LLM_PROVIDER=ollama` enables live local LLM responses.
- ChromaDB stores knowledge locally in `./chroma_db`.
- Docker Compose runs backend, frontend, and Ollama.
- Logging uses Python standard logging through `configs.logging`.
- The default demo opportunity is Northstar Telecom `SF-OPP-001`.
- Demo data now includes multiple telecom accounts and multiple opportunities per account.
- One opportunity can have multiple CPQ quote versions.
- One finalized quote can produce one placed order.
- Mock prices are fictional and intended only for demonstration.
- External system identifiers must make source ownership obvious:
  - Salesforce Account: `sf_account_id`
  - Salesforce Opportunity: `sf_opportunity_id`
  - Oracle CPQ Quote: `oracle_quote_id`
  - Oracle CPQ Order: `oracle_order_id`
- Internal database primary keys must be separate from external IDs.

---

## 6.1 Data Ownership And Linking Keys

The app sits between Salesforce CRM Cloud and Oracle CPQ Cloud. The UI, API, database, and agent state must preserve ownership boundaries through explicit key names.

Salesforce-owned records:
- Account uses `sf_account_id`
- Opportunity uses `sf_opportunity_id`
- Opportunity links to Account through `sf_account_id`

Oracle-owned records:
- Quote uses `oracle_quote_id`
- Order uses `oracle_order_id`
- Quote links to Opportunity through `sf_opportunity_id`
- Order links to Quote through `oracle_quote_id`
- Order links back to Opportunity through `sf_opportunity_id`

Application-owned records:
- Agent runs use `run_id`
- Activity events use `activity_id`
- Internal database rows may use local `id` columns, but external API payloads and frontend state should prefer the explicit source-owned names above.

Canonical business relationship:

```text
Salesforce Account sf_account_id
  -> Salesforce Opportunity sf_opportunity_id
    -> Oracle CPQ Quote oracle_quote_id
      -> Oracle CPQ Order oracle_order_id
```

---

## 7. MCP Tools

- `get_opportunity`
- `list_accounts`
- `list_opportunities`
- `recommend_products`
- `get_pricing`
- `create_quote`
- `list_quotes`
- `finalize_quote`
- `list_orders`
- `list_activity`
- `search_knowledge`

`search_knowledge` is stateless and returns:

```json
{
  "query": "string",
  "results": ["string"]
}
```

---

## 8. Agent Flow

Implemented flow:

1. Analyze intent and opportunity id.
2. Retrieve context when the query needs product, pricing, playbook, or CPQ knowledge.
3. Fetch opportunity through MCP.
4. Recommend products through MCP.
5. Calculate pricing through MCP.
6. Return recommended products and pricing for sales rep review.
7. Reprice selected products when the rep changes selections.
8. Create draft quote through MCP after sales rep approval.
9. Store created quote versions for the opportunity.
10. Finalize a selected quote and place an order through MCP.
11. Generate the final response through `LLMClient` when configured, otherwise fallback response.

Agent state includes:
- `user_input`
- `retrieved_context`
- `tools_output`
- `final_answer`
- `sf_opportunity_id`
- `opportunity`
- `recommendation`
- `pricing`
- `quote`
- `response`

---

## 9. User Experience

The frontend command center has two modes:

### Business View

Business View supports:
- Selecting an Account and then one of that account's Opportunities.
- Running an AI recommendation for the selected telecom opportunity.
- Reviewing recommended NetApp-aligned products as structured CPQ rows.
- Including/excluding products.
- Adjusting quantity and term.
- Repricing selections.
- Creating multiple draft quote versions after sales rep review.
- Viewing quote history for the current opportunity.
- Finalizing a chosen quote and placing an order.
- Viewing `oracle_quote_id`, `oracle_order_id`, `sf_opportunity_id`, total, discounts, products, pricing line items, run steps, retrieved knowledge, and assistant summary.
- Loading and error states.

### Architecture View

Architecture View supports:
- Visual trace from sales rep command through Agent, MCP, RAG, Salesforce, CPQ, LLMClient, and quote creation.
- Quote-version and order-placement steps after customer finalization.
- Layer badges that make architecture ownership explicit.
- Expandable step details showing input and output payloads.
- Layer contract panel for Agent, MCP, RAG, Tools, LLMClient, and Human approval responsibilities.
- Decision point panel for RAG trigger, CPQ rules, discounts, and sales rep approval.
- Live status based on the current recommendation, pricing, and quote state.

Successful output includes:
- Product recommendations
- Pricing breakdown
- Draft quote id
- Placed order id after quote finalization
- Agent explainability timeline
- RAG context snippets
- Architecture trace and layer contracts

---

## 10. Deployment

Local services:
- FastAPI backend on port `8000`
- Next.js frontend on port `3000`
- Ollama on port `11434`
- ChromaDB persistence under `./chroma_db`

Docker Compose:
- `backend`
- `frontend`
- `ollama`
- `chroma-db` volume
- `ollama-data` volume

---

## 11. Testing

Implemented validation includes:
- Unit tests
- Backend API tests
- Integration flow tests
- Agent graph tests
- MCP execution tests
- RAG ingestion/retrieval tests
- Logging tests
- Architecture guardrail tests
- Frontend production build
- Docker build
- Live Ollama smoke test

Latest validation:
- `78 passed`
- `npm run build` passed after the live command center update
- Live API smoke passed for Account -> Opportunity -> Recommendation -> Quote -> Finalize -> Order

---

## 12. Risks

- Local Ollama availability affects live LLM and embedding calls.
- RAG quality depends on ingested document quality.
- Mock integrations do not represent real Salesforce/Oracle CPQ authentication, schema drift, or error behavior.
- LLM responses may vary, so tests keep fallback mode deterministic.

---

## 13. Future Enhancements

- vLLM provider behind `LLMClient`
- Real Salesforce integration
- Real Oracle CPQ integration
- RBAC and audit controls
- Production observability and tracing
- OCI/Kubernetes deployment

---

## 14. Implemented Live App Data Flow

Implemented local flow:

```text
SQLite seed data
  -> Salesforce-style Account and Opportunity records
  -> Agent recommendation and pricing runs
  -> Oracle-style Quote versions
  -> Customer quote finalization
  -> Oracle-style Order placement
  -> Activity timeline and architecture trace
```

The live app should feel active because it persists:
- Account and Opportunity selection
- Generated recommendations
- Product selection edits
- Repricing actions
- Quote versions
- Finalized quote
- Placed order
- Agent run history
- Activity timeline

The UI should continue to show three ownership lanes:
- Salesforce CRM Cloud: Accounts and Opportunities
- Agentic Orchestration App: intent, MCP execution, RAG evidence, recommendations, run trace
- Oracle CPQ Cloud: Quotes, Quote Lines, Orders, Order Lines

---

## 15. Alignment

Implementation follows `FINAL_AGENTS.md`:
- Agent orchestrates only.
- MCP executes tools.
- LLM reasoning goes through `LLMClient`.
- RAG is behind MCP.
- Tests and logging are present.
