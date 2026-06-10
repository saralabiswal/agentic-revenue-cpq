"""Test coverage for official MCP audit events.

Author: Sarala Biswal
"""

import json
from pathlib import Path

from services.mcp import (
    CONFIRMATION_TOKEN_FIELD,
    MCPExecutionEngine,
    MCPToolPolicy,
    ToolDefinition,
    ToolRegistry,
    build_confirmation_token,
    execute_exposed_tool,
)


def _read_events(path: Path) -> list[dict]:
    """Read audit JSONL events from disk."""
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_official_mcp_read_only_call_writes_non_sensitive_audit_event(tmp_path) -> None:
    """Verify read-only official MCP calls write key-only audit events."""
    audit_path = tmp_path / "mcp_audit.jsonl"
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="get_opportunity",
            handler=lambda payload: {
                "sf_opportunity_id": payload["sf_opportunity_id"],
                "amount": 1250000,
            },
        )
    )

    execute_exposed_tool(
        "get_opportunity",
        {"sf_opportunity_id": "SF-OPP-SECRET"},
        execution_engine=MCPExecutionEngine(registry),
        audit_log_path=str(audit_path),
    )

    events = _read_events(audit_path)
    assert len(events) == 1
    assert events[0]["tool_name"] == "get_opportunity"
    assert events[0]["status"] == "success"
    assert events[0]["payload_keys"] == ["sf_opportunity_id"]
    assert events[0]["result_keys"] == ["amount", "sf_opportunity_id"]
    assert "SF-OPP-SECRET" not in audit_path.read_text()


def test_official_mcp_mutating_call_writes_confirmed_audit_event(tmp_path) -> None:
    """Verify confirmed mutating calls write durable audit events."""
    audit_path = tmp_path / "mcp_audit.jsonl"
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="finalize_quote",
            handler=lambda _payload: {
                "quote": {"oracle_quote_id": "ORA-Q-SECRET"},
                "order": {"oracle_order_id": "ORA-O-SECRET"},
            },
        )
    )
    payload = {"oracle_quote_id": "ORA-Q-SECRET"}
    payload[CONFIRMATION_TOKEN_FIELD] = build_confirmation_token("finalize_quote", payload)

    execute_exposed_tool(
        "finalize_quote",
        payload,
        execution_engine=MCPExecutionEngine(registry),
        policy=MCPToolPolicy(allowed_tool_names=frozenset({"finalize_quote"})),
        audit_log_path=str(audit_path),
    )

    events = _read_events(audit_path)
    assert len(events) == 1
    assert events[0]["tool_name"] == "finalize_quote"
    assert events[0]["status"] == "success"
    assert events[0]["classification"] == "mutating"
    assert events[0]["confirmed"] is True
    assert events[0]["payload_keys"] == [CONFIRMATION_TOKEN_FIELD, "oracle_quote_id"]
    assert events[0]["result_keys"] == ["order", "quote"]
    assert "ORA-Q-SECRET" not in audit_path.read_text()
    assert "ORA-O-SECRET" not in audit_path.read_text()
