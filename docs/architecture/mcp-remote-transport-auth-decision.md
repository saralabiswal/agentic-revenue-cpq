# MCP Remote Transport Auth Decision

## Status

Accepted

## Decision

The first official MCP release supports local stdio only.

Streamable HTTP or any other remote MCP transport is out of scope until a dedicated authentication, authorization, and deployment design is accepted.

## Rationale

The first MCP integration is intended for local MCP-compatible clients and MCP Inspector validation. Local stdio avoids exposing a network listener and keeps the first release focused on tool contracts, protocol wiring, and read-only capability validation.

Remote transport changes the risk model:

- External clients can discover business tools.
- Account, opportunity, quote, order, activity, and RAG data may leave the local process boundary.
- Mutating tools could create quotes or finalize orders if exposed incorrectly.
- Production deployment needs network placement, auth, authorization, audit retention, and abuse controls.

## Current Allowed Mode

Allowed:

- Local stdio MCP server.
- Read-only tools only.
- No public network binding.
- No mutating tool discovery.

Run command:

```bash
uv run python -m apps.mcp_server.main
```

## Remote Mode Requirements

Before Streamable HTTP is enabled, the implementation must define:

- Client authentication.
- Per-tool authorization.
- Network placement and allowed ingress.
- Audit retention rules.
- Rate limiting or abuse controls.
- Secret handling.
- Production logging requirements.
- Deployment-specific environment variables.

## Mutating Tool Rule

Remote MCP must not expose these tools until policy, confirmation, and durable audit controls are complete and explicitly enabled:

- `recommend_products`
- `get_pricing`
- `create_quote`
- `finalize_quote`

## Consequence

This project can validate official MCP locally now while keeping production-facing remote exposure as a later, explicit design and security task.
