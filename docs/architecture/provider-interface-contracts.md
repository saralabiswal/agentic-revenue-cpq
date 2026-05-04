# Provider Interface Contracts

Author: Sarala Biswal

## Required Interfaces

The cloud-agnostic core uses these provider boundaries:

- `AgentOrchestrator`
- `LLMClient`
- `EmbeddingClient`
- `VectorStore`
- `BusinessStore`
- `ObjectStore`
- `SecretsProvider`
- `ObservabilityProvider`

Tasks 33-38 introduce `AgentOrchestrator`, `EmbeddingClient`, `VectorStore`, `BusinessStore`, `ObjectStore`, `SecretsProvider`, and `ObservabilityProvider`. The existing `LLMClient` remains the LLM reasoning boundary.

## AgentOrchestrator

`AgentOrchestrator` owns workflow ordering and state transitions. Implementations must preserve the same state keys and response shapes used by the current API:

- `run_chat`
- `run_recommendation`
- `run_pricing`
- `run_quote_creation`

Allowed implementations:

- `langgraph`: current local/demo implementation.
- `native`: plain Python implementation that executes the same workflow through MCP.
- `oci_responses_api`: stub until an explicit OCI SDK integration task.
- `vertex_agent`: stub until an explicit GCP SDK integration task.

Agent implementations must not import Salesforce, Oracle CPQ, Chroma, Ollama, OCI, GCP, vector-store clients, or provider SDK clients directly.

## MCP And RAG

All tool calls must go through `MCPExecutionEngine`.

RAG must remain behind the MCP tool:

```text
search_knowledge
```

Agent code may request `search_knowledge` by name through MCP. It must not import RAG retrievers, vector stores, embedding clients, or database clients directly.

## LLMClient

Agent code may receive an `LLMClient` and call `chat`. It must not import provider-specific LLM clients directly.

Current supported local behavior:

- `LLM_PROVIDER=fallback`: returns no client and uses deterministic fallback responses.
- `LLM_PROVIDER=ollama`: returns the local Ollama client.

Cloud LLM providers are stubs until their explicit implementation tasks.

## EmbeddingClient

`EmbeddingClient` owns text-to-vector generation for RAG ingestion and retrieval.

Allowed implementations:

- `ollama`: local profile implementation through `OllamaEmbeddingClient`.
- `oci_genai`: stub until an explicit OCI embedding integration task.
- `vertex_ai`: stub until an explicit GCP embedding integration task.

RAG retrieval and ingestion must depend on the interface or factory, not on provider SDKs.

## VectorStore

`VectorStore` owns vector persistence and semantic lookup for the knowledge service.

Allowed implementations:

- `chroma`: local profile implementation through `ChromaVectorStore`.
- `oracle_23ai`: stub until an explicit OCI/Oracle vector integration task.
- `vertex_vector_search`: stub until an explicit GCP vector integration task.
- `pgvector`, `opensearch`, and `alloydb_vector`: portable/provider stubs.

The MCP `search_knowledge` contract remains unchanged:

```json
{
  "query": "string",
  "results": ["string"]
}
```

## BusinessStore

`BusinessStore` owns account, opportunity, quote, order, activity, and agent-run persistence.

Allowed implementations:

- `sqlite`: local profile implementation through `SQLiteBusinessStore`.
- `oracle_autonomous_db`: stub until an explicit OCI database integration task.
- `cloud_sql_postgres`: stub until an explicit GCP database integration task.
- `alloydb` and `postgres`: portable/provider stubs.

The public `services.data` API remains the repository provider boundary used by backend and integration adapters. Source-owned identifiers must remain `sf_account_id`, `sf_opportunity_id`, `oracle_quote_id`, and `oracle_order_id`.

## SecretsProvider

`SecretsProvider` owns secret lookup.

Allowed implementations:

- `env`: local profile implementation through `EnvSecretsProvider`.
- `oci_vault`: stub until an explicit OCI Vault integration task.
- `gcp_secret_manager`: stub until an explicit GCP Secret Manager integration task.

Local development reads process environment variables and does not require cloud credentials.

## ObjectStore

`ObjectStore` owns binary object storage.

Allowed implementations:

- `local_fs`: local profile implementation through `LocalFilesystemObjectStore`.
- `oci_object_storage`: stub until an explicit OCI Object Storage integration task.
- `gcs`: stub until an explicit Google Cloud Storage integration task.
- `s3_compatible`: portable/provider stub.

Local filesystem objects are rooted under `app_data/objects` by default and reject keys that escape the configured root.

## ObservabilityProvider

`ObservabilityProvider` owns logging and lightweight structured events.

Allowed implementations:

- `python_logging`: local profile implementation through `PythonLoggingObservabilityProvider`.
- `oci_logging`: stub until an explicit OCI Logging/Monitoring integration task.
- `gcp_logging`: stub until an explicit Cloud Logging/Monitoring integration task.
- `opentelemetry`: portable/provider stub.

Existing Python logging remains the local default.
