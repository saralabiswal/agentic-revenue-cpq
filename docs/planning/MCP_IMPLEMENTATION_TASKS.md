# Complete MCP Implementation Tasks

## GitHub Project Setup

Project name: `Official MCP Integration`

Project goal: introduce official Model Context Protocol support where it adds value, while preserving the existing in-process MCP-style execution boundary used by FastAPI, LangGraph, RAG, Salesforce mock integrations, and Oracle CPQ-style tools.

Recommended project fields:

| Field | Values |
| --- | --- |
| Status | Backlog, Ready, In Progress, Review, Done |
| Area | backend, mcp, rag, security, observability, docs, tests |
| Priority | P0, P1, P2 |
| Risk | low, medium, high |
| Milestone | M1 Contracts, M2 MCP Server, M3 Secure Actions, M4 External Clients |

Recommended labels:

- `mcp`
- `backend`
- `contracts`
- `security`
- `observability`
- `docs`
- `tests`
- `rag`
- `read-only`
- `mutating-tool`
- `P0`
- `P1`
- `P2`

## Task List

### M1 Contracts

#### Task 1: Audit Existing MCP-Style Tools

Labels: `mcp`, `backend`, `contracts`, `P0`

Status: Done

Description:
Inventory every tool currently registered through the internal `ToolRegistry`, classify it, and confirm whether it should be exposed through official MCP.

Scope:

- Review `services/tools/opportunity_quote.py`.
- Review `services/mcp/tools/rag_tools.py`.
- Confirm all tool names registered by `create_default_tool_registry`.
- Classify each tool as read-only or mutating.
- Identify sensitive inputs and outputs.

Acceptance criteria:

- A table exists listing every current tool name.
- Each tool has an exposure decision: expose now, expose later, or keep internal only.
- Each tool has a read-only or mutating classification.
- Mutating tools are explicitly marked as requiring security and audit controls before external MCP exposure.

Implementation:

- Added code-level audit contracts in `services/mcp/contracts.py`.
- Added `tests/test_mcp_contracts.py` coverage to verify every registered tool has a contract.

Audit table:

| Tool | Classification | Exposure decision | Sensitive data / risk notes |
| --- | --- | --- | --- |
| `list_accounts` | Read-only | Expose now | Account portfolio metadata. Local-only first. |
| `list_opportunities` | Read-only | Expose now | Opportunity list can include account-scoped pipeline metadata. |
| `get_opportunity` | Read-only | Expose now | Returns opportunity amount, requirements, risk, account summary. |
| `list_quotes` | Read-only | Expose now | Quote history and commercial totals for one opportunity. |
| `list_orders` | Read-only | Expose now | Placed-order metadata and totals. |
| `list_activity` | Read-only | Expose now | Business event timeline; no external remote exposure until auth exists. |
| `search_knowledge` | Read-only | Expose now | RAG snippets only; failures must return empty context. |
| `recommend_products` | Mutating | Expose later | Records activity, so external exposure needs policy and audit. |
| `get_pricing` | Computational | Expose later | Depends on recommendation payload; harden contract before exposure. |
| `create_quote` | Mutating | Expose later | Can persist a quote when `persist=true`; requires confirmation. |
| `finalize_quote` | Mutating | Expose later | Places an order; requires authorization, confirmation, and audit. |

#### Task 2: Define MCP Tool Input And Output Contracts

Labels: `mcp`, `contracts`, `tests`, `P0`

Status: Done

Description:
Create explicit JSON-object contracts for all tools considered for official MCP exposure.

Scope:

- Define input contracts for read-only tools first.
- Define output shape expectations for each exposed tool.
- Keep payload names aligned with the existing API and source-prefixed identifiers.
- Avoid changing existing field names such as `sf_account_id`, `sf_opportunity_id`, `oracle_quote_id`, and `oracle_order_id`.

Acceptance criteria:

- Contracts exist for `list_accounts`, `list_opportunities`, `get_opportunity`, `list_quotes`, `list_orders`, `list_activity`, and `search_knowledge`.
- Draft contracts exist for `recommend_products`, `get_pricing`, `create_quote`, and `finalize_quote`.
- Tests cover invalid payloads at the tool boundary.

Implementation:

- Added `MCP_TOOL_CONTRACTS`, `READ_ONLY_MCP_TOOL_NAMES`, and `validate_tool_payload`.
- Added schemas for the read-only exposure set and draft schemas for later mutating/computational tools.
- Added tests for full registry coverage, exposure classification, valid payloads, missing required fields, scalar type mismatches, and object type mismatches.

#### Task 3: Decide Official MCP Exposure Model

Labels: `mcp`, `architecture`, `P0`

Status: Done

Description:
Record the intended official MCP deployment model before implementation.

Recommended decision:

- Keep the current in-process `MCPExecutionEngine` for backend and agent workflows.
- Add an official MCP server adapter that delegates to the existing engine.
- Start with local stdio transport for development.
- Add Streamable HTTP only after authentication and authorization decisions are complete.

Acceptance criteria:

- Architecture decision record is added under `docs/architecture` or linked from this plan.
- Decision explicitly states whether LangGraph will continue using the internal engine.
- Decision explicitly states which transports are in scope for the first release.

Implementation:

- Added `docs/architecture/official-mcp-exposure-decision.md`.
- Decision keeps LangGraph and FastAPI on the in-process `MCPExecutionEngine`.
- Decision scopes first official MCP release to local stdio and read-only tools.

#### Task 4: Create MCP Threat Model

Labels: `mcp`, `security`, `P0`

Status: Done

Description:
Define risks and controls for exposing project tools through official MCP clients.

Scope:

- Identify data exposure risks for account, opportunity, quote, order, activity, and RAG responses.
- Identify write risks for quote creation and finalization.
- Define confirmation requirements for mutating tools.
- Define logging and audit requirements.
- Define which tools are safe for unauthenticated local-only development.

Acceptance criteria:

- Read-only tools have documented exposure rules.
- Mutating tools require policy gates before external exposure.
- Audit requirements are documented for every mutating tool call.
- Sensitive data logging rules are documented.

Implementation:

- Added `docs/architecture/mcp-threat-model.md`.
- Read-only local stdio exposure rules are documented.
- Mutating tool confirmation, authorization, and audit requirements are documented.

### M2 MCP Server

#### Task 5: Add Official MCP SDK Dependency

Labels: `mcp`, `backend`, `P0`

Status: Done

Description:
Add the official Python MCP SDK dependency and confirm the project still installs cleanly.

Scope:

- Update `pyproject.toml`.
- Update `uv.lock`.
- Confirm package import works in the project environment.
- Avoid changing unrelated dependencies.

Acceptance criteria:

- Dependency is present in `pyproject.toml`.
- Lockfile is updated.
- Existing tests still pass.

Implementation note:

- Attempted `uv add "mcp[cli]"`, matching the official Python SDK README guidance.
- Retried successfully on 2026-06-10.
- Added `mcp[cli]>=1.27.2` to `pyproject.toml`.
- Updated `uv.lock`.
- Confirmed `import mcp` works in the project environment.

#### Task 6: Create Official MCP Server Entrypoint

Labels: `mcp`, `backend`, `P0`

Status: Done

Description:
Create a server entrypoint that exposes selected tools through official MCP while delegating execution to the existing internal engine.

Recommended location:

- `apps/mcp_server/__init__.py`
- `apps/mcp_server/main.py`

Scope:

- Instantiate the existing default MCP engine.
- Register official MCP tools for the approved read-only tool list.
- Keep business logic inside the existing tool handlers.
- Keep the server adapter thin.

Acceptance criteria:

- MCP server can start locally.
- MCP tool discovery lists approved read-only tools.
- Tool execution delegates to `MCPExecutionEngine`.
- No Salesforce, CPQ, RAG, or repository logic is duplicated in the server adapter.

Implementation note:

- Added `apps/mcp_server/__init__.py`.
- Added `apps/mcp_server/main.py`.
- Entrypoint uses a lazy `FastMCP` import so tests can run before `mcp[cli]` is installed.
- Validated `create_mcp_server()` against installed MCP SDK.
- Validated SDK-backed tool discovery with `FastMCP.list_tools`.
- Validated local stdio startup with `uv run python -m apps.mcp_server.main`.

#### Task 7: Add Tool Registry To Official MCP Mapping Layer

Labels: `mcp`, `backend`, `contracts`, `P0`

Status: Done

Description:
Add a small adapter that maps internal `ToolDefinition` entries to official MCP tools.

Scope:

- Convert selected internal tool names into official MCP tool registrations.
- Preserve tool descriptions from `ToolDefinition` where possible.
- Validate payloads before calling the internal engine.
- Normalize exceptions into MCP-friendly errors.

Acceptance criteria:

- Adapter exposes read-only tools without duplicating handler code.
- Unknown tools fail cleanly.
- Invalid payloads fail cleanly.
- Errors do not leak secrets or stack traces to clients.

Implementation:

- Added `services/mcp/official_adapter.py`.
- Added `list_exposed_tool_contracts` and `execute_exposed_tool`.
- Adapter validates payloads with `validate_tool_payload`, denies non-exposed tools, delegates to `MCPExecutionEngine`, and logs payload/result keys.
- Added `tests/test_mcp_official_adapter.py`.

#### Task 8: Expose Read-Only Business Tools

Labels: `mcp`, `read-only`, `backend`, `P0`

Status: Done

Description:
Expose the low-risk read-only business tools through official MCP.

Tools:

- `list_accounts`
- `list_opportunities`
- `get_opportunity`
- `list_quotes`
- `list_orders`
- `list_activity`

Acceptance criteria:

- Each listed tool is discoverable through MCP.
- Each listed tool can be called successfully with valid input.
- Each listed tool rejects invalid input.
- Integration tests cover at least one successful call and one failure path.

Implementation note:

- Added explicit read-only wrapper functions in `apps/mcp_server/main.py`.
- Added wrapper tests in `tests/test_mcp_server_entrypoint.py`.
- Validated SDK-backed discovery for all read-only business tools.
- Validated SDK-backed `list_accounts` call through the internal engine.
- Validated invalid payload rejection through the SDK call path.

#### Task 9: Expose RAG Search Tool

Labels: `mcp`, `rag`, `read-only`, `P1`

Status: Done

Description:
Expose `search_knowledge` through official MCP with clear behavior when the local RAG stack is unavailable.

Scope:

- Register `search_knowledge`.
- Preserve existing behavior where retrieval failures return an empty result set.
- Document dependencies on embeddings, ChromaDB, and local model configuration.

Acceptance criteria:

- `search_knowledge` is discoverable through MCP.
- Valid queries return the existing result shape.
- Missing or unavailable RAG dependencies do not crash the MCP server.
- Tests cover successful retrieval with a fake retriever.

Implementation note:

- `search_knowledge` is included in the official MCP server entrypoint.
- Existing RAG fallback behavior returns empty results when local Chroma/Ollama fails.
- Validated `search_knowledge` SDK discovery.
- Validated SDK-backed `search_knowledge` result shape with a fake adapter response.

#### Task 10: Add Local Run Command

Labels: `mcp`, `docs`, `backend`, `P1`

Status: Done

Description:
Add a documented command for running the MCP server locally.

Scope:

- Add a script entry, Make target, or README command.
- Prefer a command that works with the existing `uv` workflow.
- Document required environment variables.

Acceptance criteria:

- A developer can start the MCP server from the repo root.
- The command is documented.
- The command does not require the FastAPI app to be running unless explicitly documented.

Implementation note:

- Added README command: `uv run python -m apps.mcp_server.main`.
- README documents that `uv add "mcp[cli]"` is required first.
- Validated the command starts the stdio MCP server and waits for client input.

### M3 Secure Actions

#### Task 11: Add Policy Gate For Mutating Tools

Labels: `mcp`, `security`, `mutating-tool`, `P0`

Status: Done

Description:
Add a policy gate before any mutating tool can be exposed through official MCP.

Mutating tools:

- `recommend_products`
- `get_pricing`
- `create_quote`
- `finalize_quote`

Note:
`recommend_products` currently records activity, so it should be treated as mutating even though it primarily computes recommendations.

Acceptance criteria:

- Mutating tools are not externally exposed until the gate exists.
- Policy decisions are testable.
- Denied calls return clear client-facing errors.
- Approved calls continue to use the existing internal engine.

Implementation:

- Added `MCPToolPolicy` in `services/mcp/official_adapter.py`.
- Default policy denies mutating/computational tools that are not in the read-only exposure set.
- Explicit policy approval allows a named tool to continue through `MCPExecutionEngine`.
- Added policy tests in `tests/test_mcp_official_adapter.py`.

#### Task 12: Add Confirmation Flow For Quote Creation And Finalization

Labels: `mcp`, `security`, `mutating-tool`, `P0`

Status: Done

Description:
Require explicit confirmation for quote creation and quote finalization when invoked by external MCP clients.

Scope:

- Define confirmation payload shape.
- Confirm `create_quote` behavior when `persist=true`.
- Confirm `finalize_quote` behavior before placing an order.
- Keep preview/non-persistent quote behavior separate from saved quote creation.

Acceptance criteria:

- `create_quote` with persistence requires confirmation.
- `finalize_quote` requires confirmation.
- Tests cover missing confirmation, invalid confirmation, and approved confirmation.
- Audit events identify confirmed mutating calls.

Implementation:

- Added hash-based `confirmation_token` support in `services/mcp/official_adapter.py`.
- `create_quote` requires confirmation when `persist=true`.
- `finalize_quote` always requires confirmation.
- Confirmation tokens are computed with `build_confirmation_token(tool_name, payload)`.
- Confirmation tokens are stripped before calling `MCPExecutionEngine`.
- Added missing, invalid, and approved confirmation tests.

#### Task 13: Add MCP Audit Trail

Labels: `mcp`, `observability`, `security`, `P0`

Status: Done

Description:
Record durable audit events for official MCP tool calls.

Scope:

- Log tool name, caller identity when available, payload keys, status, latency, and result keys.
- Avoid logging full sensitive payloads.
- Persist mutating call audit events where appropriate.
- Correlate MCP calls with existing agent run or activity records when available.

Acceptance criteria:

- Every official MCP tool call has structured logs.
- Mutating calls have durable audit records.
- Logs do not include secrets.
- Tests verify audit behavior for at least one read-only and one mutating call.

Implementation:

- Added `services/mcp/audit.py`.
- Official MCP adapter writes JSONL audit events with tool name, status, payload keys, result keys, classification, exposure, confirmation state, and elapsed time.
- Audit events do not store full payload or result values.
- Added `tests/test_mcp_audit.py` for read-only and confirmed mutating audit events.

#### Task 14: Add Remote Transport Auth Decision

Labels: `mcp`, `security`, `architecture`, `P1`

Status: Done

Description:
Decide whether to support Streamable HTTP transport and how clients authenticate.

Scope:

- Keep stdio local development as the first supported mode.
- Define whether remote MCP is needed.
- If remote MCP is needed, define auth, authorization, CORS/network placement, and deployment rules.

Acceptance criteria:

- Remote transport is either explicitly out of scope or has a documented auth model.
- Production deployment notes explain how the MCP server is protected.
- Mutating tools are unavailable remotely until auth and policy gates are complete.

Implementation:

- Added `docs/architecture/mcp-remote-transport-auth-decision.md`.
- Decision keeps first release on local stdio only.
- Streamable HTTP remains out of scope until authentication, authorization, network placement, and audit retention are designed.

### M4 External Clients

#### Task 15: Validate With MCP Inspector

Labels: `mcp`, `tests`, `docs`, `P0`

Status: Done

Description:
Validate the official MCP server using MCP Inspector or an equivalent MCP-compatible client.

Acceptance criteria:

- Client can connect to the local MCP server.
- Tool discovery works.
- At least one read-only business tool call works.
- `search_knowledge` behavior is validated or explicitly skipped if local RAG dependencies are unavailable.

Implementation:

- Added `scripts/validate_mcp_stdio.py`.
- Validated a real MCP client connection to `apps.mcp_server.main` over stdio.
- Validated tool discovery, `list_accounts`, and `search_knowledge`.
- `search_knowledge` returned 2 local RAG snippets after Chroma ingestion.

#### Task 16: Add MCP Integration Tests

Labels: `mcp`, `tests`, `P1`

Status: Done

Description:
Add tests that exercise the official MCP server adapter and its interaction with the existing internal engine.

Scope:

- Tool discovery test.
- Successful read-only tool call test.
- Invalid payload test.
- Unknown tool test.
- Mutating tool denied-by-default test.

Acceptance criteria:

- Tests run in the existing test suite.
- Tests do not require external network access.
- Tests use mocks or fakes for RAG dependencies where needed.

Implementation:

- Added `tests/test_mcp_stdio_integration.py`.
- Test starts `apps.mcp_server.main` over stdio with the official MCP client.
- Covers tool discovery, successful `list_accounts`, invalid `get_opportunity`, and hidden mutating `create_quote`.

#### Task 17: Decide Whether LangGraph Should Call Official MCP

Labels: `mcp`, `architecture`, `P2`

Status: Done

Description:
Evaluate whether internal LangGraph workflows should continue using `MCPExecutionEngine` directly or call the official MCP server as a client.

Recommended decision:
Keep LangGraph on the internal engine unless there is a concrete need for network isolation or shared cross-application tools.

Acceptance criteria:

- Decision is documented.
- Decision covers latency, failure modes, local development, testing, and audit impact.
- No migration is made unless benefits outweigh added operational complexity.

Implementation:

- Decision is recorded in `docs/architecture/official-mcp-exposure-decision.md`.
- LangGraph and the native orchestrator continue using the in-process `MCPExecutionEngine`.
- Official MCP is the external client protocol surface, not a replacement for internal orchestration calls.

#### Task 18: Update README And Architecture Docs

Labels: `mcp`, `docs`, `P1`

Status: Done

Description:
Update user-facing and architecture documentation after the official MCP server is implemented.

Scope:

- Explain internal MCP engine versus official MCP server.
- Document local startup.
- Document exposed tools.
- Document safety rules for mutating tools.
- Update diagrams if needed.

Acceptance criteria:

- README has a concise MCP section.
- Architecture docs describe the MCP server adapter.
- Tool exposure list is documented.
- Security notes are documented.

Implementation:

- Updated README with an `MCP Surfaces` section.
- Documented internal `MCPExecutionEngine` versus official `apps/mcp_server` stdio server.
- Documented initial exposed read-only tools.
- Documented mutating-tool safety posture.
- Architecture docs now include exposure, threat model, and remote transport auth decisions.

## Initial Tool Exposure Recommendation

Expose first:

| Tool | Classification | External MCP status |
| --- | --- | --- |
| `list_accounts` | Read-only | Expose in M2 |
| `list_opportunities` | Read-only | Expose in M2 |
| `get_opportunity` | Read-only | Expose in M2 |
| `list_quotes` | Read-only | Expose in M2 |
| `list_orders` | Read-only | Expose in M2 |
| `list_activity` | Read-only | Expose in M2 |
| `search_knowledge` | Read-only with local dependencies | Expose in M2 after RAG fallback check |

Expose later:

| Tool | Classification | External MCP status |
| --- | --- | --- |
| `recommend_products` | Mutating because it records activity | Expose after policy gate |
| `get_pricing` | Mostly computational, but depends on business payloads | Expose after contract hardening |
| `create_quote` | Mutating when `persist=true` | Expose after confirmation flow |
| `finalize_quote` | Mutating order lifecycle action | Expose after confirmation flow and audit |

## Proposed Implementation Order

1. Complete M1 contracts and threat model.
2. Add official MCP SDK dependency.
3. Create the MCP server entrypoint.
4. Add the registry-to-MCP adapter.
5. Expose read-only tools.
6. Validate with an MCP-compatible local client.
7. Add tests for discovery, success, invalid payloads, and denied mutating calls.
8. Add security gates for mutating tools.
9. Expose mutating tools only after confirmation and audit are complete.
10. Update README and architecture docs.

## Definition Of Done

The complete MCP implementation is done when:

- The project has an official MCP server entrypoint.
- Approved tools are discoverable by an MCP-compatible client.
- Tool calls delegate to the existing internal `MCPExecutionEngine`.
- Read-only tools are exposed and tested.
- Mutating tools are protected by policy, confirmation, and audit controls.
- Local developer instructions are documented.
- Architecture docs explain the difference between the internal MCP-style boundary and the official MCP protocol server.
- Existing FastAPI and LangGraph workflows continue to work without requiring external MCP transport.
