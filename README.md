# Enterprise AI Agent Platform

**Author:** Sarala Biswal

## Overview

Enterprise AI Agent Platform is a local-first opportunity-to-quote command center for enterprise sales workflows. It connects Salesforce-style account and opportunity context, RAG-backed knowledge retrieval, cloud-agnostic agent orchestration, MCP-style tool execution, and Oracle CPQ-style quote and order lifecycle automation.

The current demo is focused on a Telecom / Network Infrastructure use case with NetApp-aligned product recommendations.

## Business Problem

Enterprise opportunity-to-quote workflows often span disconnected systems:

- Salesforce CRM owns account, opportunity, customer, and pipeline context.
- Oracle CPQ owns product configuration, pricing, quotes, and orders.
- Product recommendations depend on catalog data, pricing rules, sales playbooks, and deal-specific requirements.

This fragmentation slows down sales execution, makes product recommendations difficult to explain, and reduces traceability across quote and order handoffs.

## Solution

The platform provides a governed orchestration layer between CRM, CPQ, knowledge retrieval, and LLM reasoning.

Core workflow:

1. Select a Salesforce account.
2. Choose a related opportunity.
3. Request product recommendations or use a guided next-best action.
4. Let the agent retrieve knowledge, invoke CPQ tools, calculate pricing, and explain the result.
5. Select or adjust recommended products.
6. Generate an Oracle CPQ quote.
7. Convert the finalized quote into an Oracle CPQ order.

The UI exposes both the business workflow and the technical trace so users can see agent decisions, MCP tool calls, retrieved RAG evidence, pricing results, quote versions, and ownership boundaries.

## Architecture

![Enterprise AI Agent Platform architecture](docs/assets/architecture.png)

### Architecture Documents

- [Cloud-agnostic logical architecture](docs/architecture/logical-architecture-diagram.md)
- [Cloud-agnostic physical architecture](docs/architecture/physical-architecture-diagram.md)
- [Cloud-agnostic provider architecture](docs/architecture/cloud-agnostic-provider-architecture.md)
- [Provider interface contracts](docs/architecture/provider-interface-contracts.md)
- [LangGraph workflow diagrams](docs/architecture/langgraph-workflow-diagram.md)
- [Browser-rendered workflow diagram](docs/architecture/langgraph-workflow-diagram.html)
- [OCI deployment architecture](docs/architecture/oci-deployment-architecture.md)

### Core Flow

```text
Sales Rep
  -> Next.js Workbench
  -> FastAPI Backend
  -> AgentOrchestrator
  -> MCP Tool Boundary
  -> Tools, RAG, BusinessStore, Platform Providers
  -> LLMClient response with context and execution trace
```

### Architecture Rules

- LLM reasoning goes through `LLMClient`.
- Agent orchestration goes through `AgentOrchestrator`.
- LangGraph is the default local/demo orchestrator.
- Native Python orchestration is available as a provider-safe implementation.
- MCP is the execution boundary for tools and integrations.
- RAG is reachable only through the MCP tool `search_knowledge`.
- The agent must not import Salesforce, Oracle CPQ, ChromaDB, Ollama, OCI, GCP, or vector-store clients directly.
- Runtime provider profile metadata is exposed read-only through `GET /runtime/profile`.
- Provider selection is controlled by backend deployment configuration, not by UI mutation.

## Business Object Ownership

The implementation keeps source-owned identifiers explicit:

| System | Owns | Identifier fields |
|---|---|---|
| Salesforce CRM | Accounts and opportunities | `sf_account_id`, `sf_opportunity_id` |
| Oracle CPQ | Quotes and orders | `oracle_quote_id`, `oracle_order_id` |
| Agent platform | Orchestration state, run history, activity timeline, explainability | internal run and activity IDs |

Do not introduce generic cross-system identifiers such as `account_id`, `opportunity_id`, `quote_id`, or `order_id` in API payloads.

## Runtime Profiles

The local profile is the default working profile and requires no OCI or GCP credentials.

```env
PLATFORM_PROFILE=local
AGENT_ORCHESTRATOR=langgraph
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
VECTOR_STORE_PROVIDER=chroma
BUSINESS_STORE_PROVIDER=sqlite
OBJECT_STORE_PROVIDER=local_fs
SECRETS_PROVIDER=env
OBSERVABILITY_PROVIDER=python_logging
```

`LLM_PROVIDER=fallback` remains available for deterministic tests or demos that should not call a live local LLM.

Supported platform profile names:

- `local`
- `oci`
- `gcp`
- `generic-kubernetes`

OCI and GCP profiles are currently configuration and documentation profiles with explicit stubs only. They do not add cloud SDK dependencies.

## Tech Stack

| Layer | Implementation |
|---|---|
| Frontend | Next.js, React, TypeScript |
| Backend API | FastAPI, Python 3.11 |
| Agent orchestration | `AgentOrchestrator`, LangGraph, native Python workflow |
| LLM | `LLMClient`, Ollama local default, deterministic fallback mode |
| Execution boundary | MCP execution engine and tool registry |
| Embeddings | `EmbeddingClient`, Ollama local provider |
| Vector store | `VectorStore`, ChromaDB local provider |
| Business store | `BusinessStore`, SQLite local provider |
| Object store | Local filesystem provider |
| Secrets | Environment variable provider |
| Observability | Python logging provider |
| Container runtime | Docker Compose with backend, frontend, and Ollama services |

## Repository Layout

```text
apps/backend/            FastAPI app and API endpoints
apps/frontend/           Next.js command center UI
configs/                 Logging configuration
integrations/cpq/        Oracle CPQ mock catalog, pricing, quote, and order logic
integrations/salesforce/ Salesforce CRM mock integration
schemas/                 Pydantic API contracts
services/agent/          AgentOrchestrator interface, LangGraph flow, native flow
services/business/       BusinessStore provider boundary
services/data/           SQLite schema, seed data, repositories
services/embeddings/     EmbeddingClient interface and Ollama embedding provider
services/llm/            LLMClient interface, Ollama client, LLM factory
services/mcp/            MCP execution engine, registry, and tools
services/platform/       Runtime profile config, object store, secrets, observability providers
services/rag/            Vector store, retriever, ingestion, compatibility exports
services/tools/          MCP tool handlers
docs/assets/             Architecture diagram assets
docs/architecture/       Logical, physical, provider, and deployment architecture docs
scripts/                 Diagram generation scripts
tests/                   Backend, agent, MCP, RAG, provider, and guardrail tests
```

## Prerequisites

Install these before running the local app:

- Python 3.11 or newer
- `uv`
- Node.js 24 or newer with npm
- Ollama, for local LLM reasoning and RAG embeddings
- Docker Desktop or Docker plus Compose plugin, if using the container path

Recommended Ollama models:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1
```

`nomic-embed-text` is required for local RAG ingestion and retrieval. `llama3.1` is required for the default local LLM profile.

## Local Setup

From the repository root, install Python dependencies:

```bash
uv sync --extra dev
```

Start Ollama if it is not already running:

```bash
ollama serve
```

If `ollama serve` reports that port `11434` is already in use, Ollama is already running.

Ingest the sample product catalog, pricing rules, and sales playbook documents into ChromaDB:

```bash
uv run python -m services.rag.ingest
```

Start the backend:

```bash
uv run uvicorn apps.backend.main:app --host 127.0.0.1 --port 8000
```

Use deterministic fallback responses instead of live Ollama reasoning:

```bash
LLM_PROVIDER=fallback uv run uvicorn apps.backend.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```bash
cd apps/frontend
npm ci
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Open the app:

```text
http://localhost:3000
```

## Health And Runtime Checks

Backend health:

```bash
curl -s http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

Runtime profile:

```bash
curl -s http://127.0.0.1:8000/runtime/profile
```

The runtime profile response is read-only display metadata for the UI. It does not expose secrets, tokens, credential-bearing URLs, or database connection strings.

## Docker Setup

Build and start the full stack:

```bash
docker compose up --build
```

Pull the Ollama models into the Compose Ollama service:

```bash
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull llama3.1
```

Ingest RAG knowledge into the backend Chroma volume:

```bash
docker compose exec backend python -m services.rag.ingest
```

Local URLs:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000/health
Ollama:   http://localhost:11434
```

Stop the stack:

```bash
docker compose down
```

## Validation

Run Python tests:

```bash
uv run --extra dev pytest -q
```

Run a production frontend build:

```bash
cd apps/frontend
npm run build
```

Regenerate architecture diagrams on macOS:

```bash
swift scripts/generate_architecture_diagram.swift
swift scripts/generate_logical_architecture_diagram.swift
swift scripts/generate_physical_architecture_diagram.swift
```

Generated assets:

```text
docs/assets/architecture.png
docs/assets/logical-architecture.png
docs/assets/physical-architecture.png
```

## Runtime Data

The app creates local runtime data on demand:

- SQLite business database: `app_data/business.sqlite3`
- ChromaDB vector database: `chroma_db/`
- Local object files, when used: `app_data/objects/`

These folders are ignored by git. Delete them only when you intentionally want to reset local runtime state, then restart the backend and rerun RAG ingestion.

## Corporate Network Notes

If npm or curl fails because an office network intercepts SSL, the preferred fix is to configure the company root CA certificate. For npm:

```bash
npm config set cafile /path/to/company-root-ca.pem
```

As a temporary local workaround only, disable npm strict SSL and then turn it back on after installation:

```bash
npm config set strict-ssl false
npm ci
npm config set strict-ssl true
```

## Optional Cloud Provider Profiles

The current implementation is local-first. OCI and GCP are documented provider profiles with explicit stubs only. The repository does not add OCI or GCP SDK dependencies yet.

Use these docs when replacing local settings with managed cloud services:

- [Cloud-agnostic provider architecture](docs/architecture/cloud-agnostic-provider-architecture.md)
- [Provider interface contracts](docs/architecture/provider-interface-contracts.md)
- [Cloud-agnostic logical architecture](docs/architecture/logical-architecture-diagram.md)
- [Cloud-agnostic physical architecture](docs/architecture/physical-architecture-diagram.md)
- [OCI deployment profile](docs/architecture/oci-deployment-profile.md)
- [GCP deployment profile](docs/architecture/gcp-deployment-profile.md)
- [OCI deployment architecture](docs/architecture/oci-deployment-architecture.md)

### OCI Target Components

Use `PLATFORM_PROFILE=oci` when OCI adapters are implemented.

| Capability | OCI target |
|---|---|
| Runtime | OKE or OCI Compute |
| Agent orchestration | Native Python or OCI Responses API adapter |
| LLM | OCI Generative AI |
| Embeddings | OCI Generative AI Embeddings |
| Vector store | Oracle Database 23ai Vector Search or OCI OpenSearch |
| Business store | Autonomous Database or Oracle Database |
| Object store | OCI Object Storage |
| Secrets | OCI Vault |
| Observability | OCI Logging / Monitoring / APM |

Example OCI profile:

```env
PLATFORM_PROFILE=oci
AGENT_ORCHESTRATOR=native
LLM_PROVIDER=oci_genai
EMBEDDING_PROVIDER=oci_genai
VECTOR_STORE_PROVIDER=oracle_23ai
BUSINESS_STORE_PROVIDER=oracle_autonomous_db
OBJECT_STORE_PROVIDER=oci_object_storage
SECRETS_PROVIDER=oci_vault
OBSERVABILITY_PROVIDER=oci_logging
```

### GCP Target Components

Use `PLATFORM_PROFILE=gcp` when GCP adapters are implemented.

| Capability | GCP target |
|---|---|
| Runtime | Cloud Run or GKE |
| Agent orchestration | Native Python or Vertex Agent adapter |
| LLM | Vertex AI Gemini |
| Embeddings | Vertex AI Embeddings |
| Vector store | Vertex AI Vector Search, AlloyDB vector, or pgvector |
| Business store | Cloud SQL PostgreSQL or AlloyDB |
| Object store | Cloud Storage |
| Secrets | Secret Manager |
| Observability | Cloud Logging / Monitoring / Trace |

Example GCP profile:

```env
PLATFORM_PROFILE=gcp
AGENT_ORCHESTRATOR=native
LLM_PROVIDER=vertex_ai
EMBEDDING_PROVIDER=vertex_ai
VECTOR_STORE_PROVIDER=vertex_vector_search
BUSINESS_STORE_PROVIDER=cloud_sql_postgres
OBJECT_STORE_PROVIDER=gcs
SECRETS_PROVIDER=gcp_secret_manager
OBSERVABILITY_PROVIDER=gcp_logging
```

Provider profile changes must not change FastAPI route names, frontend payload field names, MCP tool names, RAG access through `search_knowledge`, or source-prefixed identifiers such as `sf_account_id`, `sf_opportunity_id`, `oracle_quote_id`, and `oracle_order_id`.
