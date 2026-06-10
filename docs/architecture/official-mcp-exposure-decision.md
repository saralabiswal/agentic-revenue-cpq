# Official MCP Exposure Decision

## Status

Accepted

## Context

The project already has an in-process MCP-style execution boundary:

- `services/mcp/engine.py` executes named tools.
- `services/mcp/registry.py` stores tool definitions.
- `services/tools/opportunity_quote.py` registers Salesforce-style, CPQ-style, quote, order, and activity tools.
- `services/mcp/tools/rag_tools.py` exposes RAG through `search_knowledge`.

This boundary is used by FastAPI routes and LangGraph/native agent workflows. It is intentionally local and in-process, which keeps the demo simple, testable, and auditable.

The next implementation phase is to expose selected capabilities through the official Model Context Protocol so external MCP-compatible clients can discover and invoke approved tools.

## Decision

Keep the current in-process `MCPExecutionEngine` as the backend and agent execution boundary.

Add an official MCP server adapter as a thin protocol layer around the existing registry and engine.

The official MCP adapter must:

- Delegate tool execution to `MCPExecutionEngine`.
- Use `services.mcp.contracts.MCP_TOOL_CONTRACTS` for exposure decisions and payload validation.
- Expose only `READ_ONLY_MCP_TOOL_NAMES` in the first release.
- Avoid duplicating Salesforce, CPQ, RAG, repository, or pricing logic.
- Preserve existing tool names and source-prefixed identifiers such as `sf_account_id`, `sf_opportunity_id`, `oracle_quote_id`, and `oracle_order_id`.

## Transport Scope

First release:

- Local stdio transport for development and MCP Inspector validation.

Out of scope until security work is complete:

- Streamable HTTP transport.
- Remote MCP clients.
- Mutating tool exposure.

## LangGraph Decision

LangGraph and the native orchestrator will continue calling the in-process `MCPExecutionEngine` directly.

Reasoning:

- Internal workflows do not need a network hop to call local business tools.
- Existing tests already validate the internal engine boundary.
- Keeping LangGraph in-process avoids adding latency and protocol failure modes to the core app.
- The official MCP server is for external MCP clients, not for replacing the internal workflow boundary.

## Initial External Exposure

Expose now:

- `list_accounts`
- `list_opportunities`
- `get_opportunity`
- `list_quotes`
- `list_orders`
- `list_activity`
- `search_knowledge`

Expose later after policy, confirmation, and audit controls:

- `recommend_products`
- `get_pricing`
- `create_quote`
- `finalize_quote`

## Consequences

Positive:

- External MCP support can be added without destabilizing FastAPI or LangGraph flows.
- Tool logic remains in one place.
- Read-only tools can be validated early with low business risk.
- Mutating actions remain protected until explicit controls exist.

Tradeoffs:

- There will be two execution surfaces: internal in-process calls and official MCP protocol calls.
- Contract metadata must stay aligned with registered tool names.
- Remote MCP support requires a separate auth and deployment decision.

## Validation

Implementation must include:

- Contract coverage tests proving every registered tool has an exposure contract.
- MCP adapter tests for discovery, valid calls, invalid payloads, and denied mutating calls.
- Documentation for local startup and exposed tools.
