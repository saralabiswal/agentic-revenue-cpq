"""Adapter helpers for exposing internal tools through official MCP.

Author: Sarala Biswal
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

from services.mcp.audit import create_audit_event, record_mcp_audit_event
from services.mcp.contracts import (
    MCP_TOOL_CONTRACTS,
    READ_ONLY_MCP_TOOL_NAMES,
    ToolContract,
    ToolContractError,
    get_tool_contract,
    validate_tool_payload,
)
from services.mcp.engine import MCPExecutionEngine, ToolExecutionError
from services.mcp.factory import create_default_mcp_engine


logger = logging.getLogger(__name__)
CONFIRMATION_TOKEN_FIELD = "confirmation_token"


class OfficialMCPAdapterError(ValueError):
    """Raised when an external MCP request is denied or invalid."""


@dataclass(frozen=True)
class MCPToolPolicy:
    """Explicit policy for tools outside the first read-only MCP exposure set."""

    allowed_tool_names: frozenset[str] = field(default_factory=frozenset)

    def allows(self, contract: ToolContract) -> bool:
        """Return whether the policy allows this non-default tool."""
        return contract.name in self.allowed_tool_names


def list_exposed_tool_contracts() -> list[ToolContract]:
    """Return contracts for tools approved for first-release official MCP exposure."""
    return [MCP_TOOL_CONTRACTS[tool_name] for tool_name in READ_ONLY_MCP_TOOL_NAMES]


def build_confirmation_token(tool_name: str, payload: dict[str, Any] | None) -> str:
    """Build a deterministic confirmation token for one exact tool payload."""
    canonical_payload = {
        key: value
        for key, value in (payload or {}).items()
        if key != CONFIRMATION_TOKEN_FIELD
    }
    encoded = json.dumps(
        {
            "tool_name": tool_name,
            "payload": canonical_payload,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def execute_exposed_tool(
    tool_name: str,
    payload: dict[str, Any] | None = None,
    execution_engine: MCPExecutionEngine | None = None,
    policy: MCPToolPolicy | None = None,
    audit_log_path: str | None = None,
) -> dict[str, Any]:
    """Validate and execute one tool approved for external MCP exposure."""
    started_at = time.perf_counter()
    contract: ToolContract | None = None
    confirmed = False
    try:
        contract = get_tool_contract(tool_name)
        active_policy = policy or MCPToolPolicy()
        if contract.exposure != "expose_now" and not active_policy.allows(contract):
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            _record_audit(
                tool_name=tool_name,
                status="denied",
                payload=payload,
                elapsed_ms=elapsed_ms,
                contract=contract,
                audit_log_path=audit_log_path,
            )
            logger.warning(
                "Official MCP tool denied: tool=%s exposure=%s",
                tool_name,
                contract.exposure,
            )
            raise OfficialMCPAdapterError(f"Tool is not externally exposed: {tool_name}")

        validated_payload = validate_tool_payload(tool_name, payload)
        if _requires_confirmation(tool_name, validated_payload):
            expected_token = build_confirmation_token(tool_name, validated_payload)
            if validated_payload.get(CONFIRMATION_TOKEN_FIELD) != expected_token:
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                _record_audit(
                    tool_name=tool_name,
                    status="denied",
                    payload=validated_payload,
                    elapsed_ms=elapsed_ms,
                    contract=contract,
                    audit_log_path=audit_log_path,
                )
                logger.warning("Official MCP tool confirmation missing or invalid: tool=%s", tool_name)
                raise OfficialMCPAdapterError(f"Tool confirmation is required: {tool_name}")
            confirmed = True

        engine_payload = {
            key: value
            for key, value in validated_payload.items()
            if key != CONFIRMATION_TOKEN_FIELD
        }
        engine = execution_engine or create_default_mcp_engine()
        result = engine.execute(tool_name, engine_payload)
    except ToolContractError as exc:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        _record_audit(
            tool_name=tool_name,
            status="validation_error",
            payload=payload,
            elapsed_ms=elapsed_ms,
            contract=contract,
            error=str(exc),
            audit_log_path=audit_log_path,
        )
        logger.info("Official MCP tool validation failed: tool=%s error=%s", tool_name, exc)
        raise OfficialMCPAdapterError(str(exc)) from exc
    except ToolExecutionError as exc:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        _record_audit(
            tool_name=tool_name,
            status="execution_error",
            payload=payload,
            elapsed_ms=elapsed_ms,
            contract=contract,
            error=str(exc),
            confirmed=confirmed,
            audit_log_path=audit_log_path,
        )
        logger.info("Official MCP tool execution failed: tool=%s", tool_name)
        raise OfficialMCPAdapterError(str(exc)) from exc

    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    _record_audit(
        tool_name=tool_name,
        status="success",
        payload=payload,
        result=result,
        elapsed_ms=elapsed_ms,
        contract=contract,
        confirmed=confirmed,
        audit_log_path=audit_log_path,
    )
    logger.info(
        "Official MCP tool completed: tool=%s payload_keys=%s result_keys=%s elapsed_ms=%s",
        tool_name,
        sorted((payload or {}).keys()),
        sorted(result.keys()),
        elapsed_ms,
    )
    return result


def _requires_confirmation(tool_name: str, payload: dict[str, Any]) -> bool:
    """Return whether a policy-approved external tool call needs confirmation."""
    if tool_name == "finalize_quote":
        return True
    if tool_name == "create_quote":
        return bool(payload.get("persist", False))
    return False


def _record_audit(
    *,
    tool_name: str,
    status: str,
    payload: dict[str, Any] | None,
    elapsed_ms: int,
    contract: ToolContract | None,
    audit_log_path: str | None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    confirmed: bool = False,
) -> None:
    """Persist a non-sensitive official MCP audit event."""
    event = create_audit_event(
        tool_name=tool_name,
        status=status,
        payload=payload,
        result=result,
        elapsed_ms=elapsed_ms,
        classification=contract.classification if contract else None,
        exposure=contract.exposure if contract else None,
        error=error,
        confirmed=confirmed,
    )
    record_mcp_audit_event(event, audit_log_path=audit_log_path)
