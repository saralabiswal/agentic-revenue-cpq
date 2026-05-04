# OCI Deployment Profile

Author: Sarala Biswal

## Purpose

The OCI profile describes how the cloud-agnostic platform can run on Oracle Cloud Infrastructure without making OCI a dependency of the local profile. The current local Docker Compose application remains the default working profile.

## Profile Selection

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

These provider values select adapter boundaries. OCI SDK integrations are intentionally stubs until explicit implementation tasks add them.

## Component Mapping

| Capability | Local Default | OCI Target |
|---|---|---|
| Runtime | Docker Compose | OKE or OCI Compute |
| API edge | local FastAPI/CORS | OCI API Gateway or Load Balancer |
| Agent orchestration | LangGraph / native | native Python or OCI Responses API adapter |
| LLM | Ollama | OCI Generative AI |
| Embeddings | Ollama | OCI Generative AI embeddings |
| Vector store | ChromaDB | Oracle Database 23ai or OCI OpenSearch |
| Business store | SQLite | Oracle Autonomous Database |
| Object store | local filesystem | OCI Object Storage |
| Secrets | environment variables | OCI Vault |
| Observability | Python logging | OCI Logging, Monitoring, and APM |
| Container registry | local Docker | OCI Container Registry |

## Runtime

FastAPI and the frontend can be deployed as containers to OKE or OCI Compute. The container image should keep the same API routes, MCP tool names, and frontend payloads used by the local demo.

OCI API Gateway or an OCI Load Balancer may sit in front of FastAPI. That edge layer must not rewrite business identifiers or payload shapes.

## Provider Paths

`AGENT_ORCHESTRATOR=native` uses the plain Python workflow and keeps tool execution behind MCP. An `oci_responses_api` orchestrator can be added later as a provider adapter, but it must preserve the `AgentOrchestrator` interface.

`LLM_PROVIDER=oci_genai` and `EMBEDDING_PROVIDER=oci_genai` target OCI Generative AI. Agent code must continue to use `LLMClient` and RAG code must continue to use `EmbeddingClient`.

`VECTOR_STORE_PROVIDER=oracle_23ai` targets Oracle Database 23ai vector capabilities. OCI OpenSearch can be added as an alternate provider behind the same `VectorStore` contract.

`BUSINESS_STORE_PROVIDER=oracle_autonomous_db` targets Autonomous Database for account, opportunity, quote, order, activity, and agent-run persistence. The source-owned ID names remain `sf_account_id`, `sf_opportunity_id`, `oracle_quote_id`, and `oracle_order_id`.

`OBJECT_STORE_PROVIDER=oci_object_storage`, `SECRETS_PROVIDER=oci_vault`, and `OBSERVABILITY_PROVIDER=oci_logging` map local filesystem objects, environment secrets, and Python logging to OCI Object Storage, Vault, and Logging/Monitoring/APM.

## Guardrails

The OCI profile must not change:

- FastAPI route contracts.
- MCP tool names or payload contracts.
- Frontend payload field names.
- Source-owned business identifiers.
- The rule that RAG is accessed only through MCP `search_knowledge`.
- The rule that LLM calls go through `LLMClient`.

OCI SDK imports, when added, must live only in provider-specific adapter modules.
