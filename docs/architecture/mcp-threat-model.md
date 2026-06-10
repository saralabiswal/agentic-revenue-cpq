# MCP Threat Model

## Scope

This threat model covers the planned official MCP server adapter for this project.

In scope:

- External MCP discovery of approved tools.
- External MCP invocation of approved read-only tools.
- Future exposure of mutating tools after policy, confirmation, and audit controls exist.

Out of scope for the first release:

- Public internet exposure.
- Remote Streamable HTTP transport.
- Third-party identity provider integration.
- Direct database, Salesforce, CPQ, or vector-store access outside registered tools.

## Assets

| Asset | Risk |
| --- | --- |
| Account records | Customer/account metadata exposure. |
| Opportunity records | Pipeline, amount, requirements, risk, and close-date exposure. |
| Quote records | Commercial terms, totals, status, and quote identifiers. |
| Order records | Order lifecycle metadata and commercial outcome exposure. |
| Activity timeline | Business-event history and operational trace exposure. |
| RAG snippets | Product, pricing, and sales playbook content exposure. |
| Quote creation | Persistent commercial artifact creation. |
| Quote finalization | Order placement. |

## Trust Boundaries

Internal trusted boundaries:

- FastAPI route handlers.
- LangGraph/native orchestrators.
- `MCPExecutionEngine`.
- Internal tool handlers.

External or semi-trusted boundaries:

- MCP-compatible clients.
- Local MCP Inspector.
- Future remote MCP transport.

The official MCP server adapter must be treated as an external boundary even when it starts as a local-only stdio process.

## Initial Exposure Rules

Read-only tools may be exposed locally first:

- `list_accounts`
- `list_opportunities`
- `get_opportunity`
- `list_quotes`
- `list_orders`
- `list_activity`
- `search_knowledge`

Mutating or action-like tools must remain disabled for external MCP until security controls are complete:

- `recommend_products`
- `get_pricing`
- `create_quote`
- `finalize_quote`

`recommend_products` is classified as mutating because it records business activity.

`get_pricing` is computational, but it should remain expose-later until the external recommendation payload contract is hardened.

## Threats And Controls

| Threat | Example | Required control |
| --- | --- | --- |
| Overexposure through discovery | Client discovers tools not intended for external use. | Official adapter registers only `READ_ONLY_MCP_TOOL_NAMES` in first release. |
| Invalid payload execution | Client sends wrong field types or missing identifiers. | Validate with `validate_tool_payload` before engine execution. |
| Sensitive payload logging | Full opportunity or quote payload appears in logs. | Log tool name, payload keys, status, latency, and result keys only. |
| Business write without approval | Client creates or finalizes quote directly. | Do not register mutating tools until policy and confirmation exist. |
| Replay of mutating action | Client repeats quote finalization. | Require idempotency/audit review before external mutating exposure. |
| RAG dependency failure | Chroma/Ollama fails and breaks recommendation flow. | `search_knowledge` returns an empty result set on retrieval failure. |
| Unknown tool access | Client calls unregistered or internal tool name. | Return controlled error without stack trace. |
| Remote unauthenticated access | HTTP MCP server is exposed without auth. | Keep remote transport out of scope until auth model is accepted. |

## Confirmation Requirements

Before external MCP exposure:

- `create_quote` with `persist=true` must require explicit confirmation.
- `finalize_quote` must require explicit confirmation.
- Confirmation must be tied to the exact action payload.
- Confirmation failures must be audited as denied attempts.

## Audit Requirements

Every official MCP call should log:

- Tool name.
- Caller identity when available.
- Payload keys, not full payload values.
- Result keys, not full result values.
- Status: success, denied, validation_error, execution_error.
- Latency.

Mutating tool calls must additionally persist durable audit records before external exposure.

## Local Development Rule

Local stdio MCP may run without remote authentication only when:

- It binds no public network port.
- It exposes read-only tools only.
- Mutating tools are absent from discovery.
- The server runs with the same local data assumptions as the FastAPI demo.

## Remote Transport Rule

Streamable HTTP or any remote MCP transport requires a new implementation task and must define:

- Authentication.
- Authorization.
- Network placement.
- Allowed clients.
- Rate limiting or abuse controls.
- Production logging and audit retention.
