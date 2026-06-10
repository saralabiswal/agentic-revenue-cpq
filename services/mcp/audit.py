"""Audit helpers for official MCP tool calls.

Author: Sarala Biswal
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MCPAuditEvent:
    """Non-sensitive audit record for one official MCP tool call."""

    tool_name: str
    status: str
    payload_keys: list[str]
    result_keys: list[str]
    elapsed_ms: int
    classification: str | None = None
    exposure: str | None = None
    caller: str | None = None
    error: str | None = None
    confirmed: bool = False
    created_at: str = ""


def create_audit_event(
    *,
    tool_name: str,
    status: str,
    payload: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    elapsed_ms: int = 0,
    classification: str | None = None,
    exposure: str | None = None,
    caller: str | None = None,
    error: str | None = None,
    confirmed: bool = False,
) -> MCPAuditEvent:
    """Build an audit event without storing sensitive payload or result values."""
    return MCPAuditEvent(
        tool_name=tool_name,
        status=status,
        payload_keys=sorted((payload or {}).keys()),
        result_keys=sorted((result or {}).keys()),
        elapsed_ms=elapsed_ms,
        classification=classification,
        exposure=exposure,
        caller=caller,
        error=error,
        confirmed=confirmed,
        created_at=datetime.now(UTC).isoformat(),
    )


def record_mcp_audit_event(
    event: MCPAuditEvent,
    audit_log_path: str | Path | None = None,
) -> None:
    """Append one MCP audit event to the configured JSONL log."""
    path = Path(audit_log_path or os.getenv("MCP_AUDIT_LOG_PATH", "app_data/mcp_audit.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), sort_keys=True))
        handle.write("\n")
