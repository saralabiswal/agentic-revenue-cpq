# GCP Deployment Profile

Author: Sarala Biswal

## Purpose

The GCP profile describes how the cloud-agnostic platform can run on Google Cloud without making GCP a dependency of the local profile. The current local Docker Compose application remains the default working profile.

## Profile Selection

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

These provider values select adapter boundaries. GCP SDK integrations are intentionally stubs until explicit implementation tasks add them.

## Component Mapping

| Capability | Local Default | GCP Target |
|---|---|---|
| Runtime | Docker Compose | Cloud Run or GKE |
| API edge | local FastAPI/CORS | API Gateway, Apigee, or Cloud Load Balancing |
| Agent orchestration | LangGraph / native | native Python or Vertex Agent adapter |
| LLM | Ollama | Vertex AI Gemini |
| Embeddings | Ollama | Vertex AI Embeddings |
| Vector store | ChromaDB | Vertex AI Vector Search, AlloyDB vector, or pgvector |
| Business store | SQLite | Cloud SQL for PostgreSQL or AlloyDB |
| Object store | local filesystem | Cloud Storage |
| Secrets | environment variables | Secret Manager |
| Observability | Python logging | Cloud Logging, Monitoring, and Trace |
| Container registry | local Docker | Artifact Registry |

## Runtime

FastAPI and the frontend can be deployed as containers to Cloud Run or GKE. The container image should keep the same API routes, MCP tool names, and frontend payloads used by the local demo.

API Gateway, Apigee, or Cloud Load Balancing may sit in front of FastAPI. That edge layer must not rewrite business identifiers or payload shapes.

## Provider Paths

`AGENT_ORCHESTRATOR=native` uses the plain Python workflow and keeps tool execution behind MCP. A `vertex_agent` orchestrator can be added later as a provider adapter, but it must preserve the `AgentOrchestrator` interface.

`LLM_PROVIDER=vertex_ai` targets Vertex AI Gemini. Agent code must continue to use `LLMClient`.

`EMBEDDING_PROVIDER=vertex_ai` targets Vertex AI Embeddings. RAG ingestion and retrieval must continue to use `EmbeddingClient`.

`VECTOR_STORE_PROVIDER=vertex_vector_search` targets Vertex AI Vector Search. AlloyDB vector and pgvector can be added as alternate providers behind the same `VectorStore` contract.

`BUSINESS_STORE_PROVIDER=cloud_sql_postgres` targets Cloud SQL for PostgreSQL. AlloyDB can be added as another provider behind the same `BusinessStore` contract. The source-owned ID names remain `sf_account_id`, `sf_opportunity_id`, `oracle_quote_id`, and `oracle_order_id`.

`OBJECT_STORE_PROVIDER=gcs`, `SECRETS_PROVIDER=gcp_secret_manager`, and `OBSERVABILITY_PROVIDER=gcp_logging` map local filesystem objects, environment secrets, and Python logging to Cloud Storage, Secret Manager, and Cloud Logging/Monitoring/Trace.

## Guardrails

The GCP profile must not change:

- FastAPI route contracts.
- MCP tool names or payload contracts.
- Frontend payload field names.
- Source-owned business identifiers.
- The rule that RAG is accessed only through MCP `search_knowledge`.
- The rule that LLM calls go through `LLMClient`.

GCP SDK imports, when added, must live only in provider-specific adapter modules.
