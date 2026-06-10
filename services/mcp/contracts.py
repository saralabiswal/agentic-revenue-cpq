"""Contracts for tools that may be exposed through official MCP.

Author: Sarala Biswal
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ToolClassification = Literal["read_only", "mutating", "computational"]
ToolExposure = Literal["expose_now", "expose_later", "internal_only"]


class ToolContractError(ValueError):
    """Raised when a tool payload does not match its MCP exposure contract."""


@dataclass(frozen=True)
class ToolContract:
    """Stable MCP exposure contract for one internal tool."""

    name: str
    classification: ToolClassification
    exposure: ToolExposure
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    required_fields: tuple[str, ...] = ()
    string_fields: tuple[str, ...] = ()
    object_fields: tuple[str, ...] = ()
    boolean_fields: tuple[str, ...] = ()
    integer_fields: tuple[str, ...] = ()
    notes: str = ""


def _object_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    """Build a JSON-object schema fragment for tool inputs or outputs."""
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": True,
    }


MCP_TOOL_CONTRACTS: dict[str, ToolContract] = {
    "list_accounts": ToolContract(
        name="list_accounts",
        classification="read_only",
        exposure="expose_now",
        input_schema=_object_schema({}),
        output_schema=_object_schema({"accounts": {"type": "array"}}, ["accounts"]),
        notes="Safe local MCP read path for Salesforce-style account selector data.",
    ),
    "list_opportunities": ToolContract(
        name="list_opportunities",
        classification="read_only",
        exposure="expose_now",
        input_schema=_object_schema({"sf_account_id": {"type": "string"}}),
        output_schema=_object_schema({"opportunities": {"type": "array"}}, ["opportunities"]),
        string_fields=("sf_account_id",),
        notes="Optional account scope keeps portfolio reads bounded when supplied.",
    ),
    "get_opportunity": ToolContract(
        name="get_opportunity",
        classification="read_only",
        exposure="expose_now",
        input_schema=_object_schema({"sf_opportunity_id": {"type": "string"}}, ["sf_opportunity_id"]),
        output_schema=_object_schema({"sf_opportunity_id": {"type": "string"}}),
        required_fields=("sf_opportunity_id",),
        string_fields=("sf_opportunity_id",),
        notes="Returns one Salesforce-style opportunity and account summary.",
    ),
    "list_quotes": ToolContract(
        name="list_quotes",
        classification="read_only",
        exposure="expose_now",
        input_schema=_object_schema({"sf_opportunity_id": {"type": "string"}}, ["sf_opportunity_id"]),
        output_schema=_object_schema({"quotes": {"type": "array"}}, ["quotes"]),
        required_fields=("sf_opportunity_id",),
        string_fields=("sf_opportunity_id",),
        notes="Read-only quote history for one opportunity.",
    ),
    "list_orders": ToolContract(
        name="list_orders",
        classification="read_only",
        exposure="expose_now",
        input_schema=_object_schema({"sf_opportunity_id": {"type": "string"}}),
        output_schema=_object_schema({"orders": {"type": "array"}}, ["orders"]),
        string_fields=("sf_opportunity_id",),
        notes="Optional opportunity scope for placed-order reads.",
    ),
    "list_activity": ToolContract(
        name="list_activity",
        classification="read_only",
        exposure="expose_now",
        input_schema=_object_schema(
            {
                "sf_opportunity_id": {"type": "string"},
                "sf_account_id": {"type": "string"},
            }
        ),
        output_schema=_object_schema({"activity": {"type": "array"}}, ["activity"]),
        string_fields=("sf_opportunity_id", "sf_account_id"),
        notes="Activity can include business event metadata, so external exposure stays local-only first.",
    ),
    "search_knowledge": ToolContract(
        name="search_knowledge",
        classification="read_only",
        exposure="expose_now",
        input_schema=_object_schema(
            {
                "query": {"type": "string"},
                "k": {"type": "integer", "minimum": 1},
            },
            ["query"],
        ),
        output_schema=_object_schema(
            {
                "query": {"type": "string"},
                "results": {"type": "array", "items": {"type": "string"}},
            },
            ["query", "results"],
        ),
        required_fields=("query",),
        string_fields=("query",),
        integer_fields=("k",),
        notes="RAG failures must return an empty result set instead of failing the workflow.",
    ),
    "recommend_products": ToolContract(
        name="recommend_products",
        classification="mutating",
        exposure="expose_later",
        input_schema=_object_schema({"opportunity": {"type": "object"}}, ["opportunity"]),
        output_schema=_object_schema(
            {
                "sf_opportunity_id": {"type": "string"},
                "products": {"type": "array"},
                "currency": {"type": "string"},
            }
        ),
        required_fields=("opportunity",),
        object_fields=("opportunity",),
        notes="Records activity, so external MCP exposure requires policy and audit controls.",
    ),
    "get_pricing": ToolContract(
        name="get_pricing",
        classification="computational",
        exposure="expose_later",
        input_schema=_object_schema({"recommendation": {"type": "object"}}, ["recommendation"]),
        output_schema=_object_schema(
            {
                "sf_opportunity_id": {"type": "string"},
                "line_items": {"type": "array"},
                "total": {"type": "number"},
            }
        ),
        required_fields=("recommendation",),
        object_fields=("recommendation",),
        notes="Expose after recommendation payload shape is hardened for external clients.",
    ),
    "create_quote": ToolContract(
        name="create_quote",
        classification="mutating",
        exposure="expose_later",
        input_schema=_object_schema(
            {
                "pricing": {"type": "object"},
                "persist": {"type": "boolean"},
            },
            ["pricing"],
        ),
        output_schema=_object_schema(
            {
                "oracle_quote_id": {"type": "string"},
                "sf_opportunity_id": {"type": "string"},
                "status": {"type": "string"},
            }
        ),
        required_fields=("pricing",),
        object_fields=("pricing",),
        boolean_fields=("persist",),
        notes="Persistent quote creation requires explicit confirmation before external MCP exposure.",
    ),
    "finalize_quote": ToolContract(
        name="finalize_quote",
        classification="mutating",
        exposure="expose_later",
        input_schema=_object_schema({"oracle_quote_id": {"type": "string"}}, ["oracle_quote_id"]),
        output_schema=_object_schema(
            {
                "quote": {"type": "object"},
                "order": {"type": "object"},
            }
        ),
        required_fields=("oracle_quote_id",),
        string_fields=("oracle_quote_id",),
        notes="Places an order and must require confirmation, authorization, and audit.",
    ),
}


READ_ONLY_MCP_TOOL_NAMES: tuple[str, ...] = tuple(
    name
    for name, contract in MCP_TOOL_CONTRACTS.items()
    if contract.exposure == "expose_now"
)


def get_tool_contract(tool_name: str) -> ToolContract:
    """Return the exposure contract for a tool name."""
    try:
        return MCP_TOOL_CONTRACTS[tool_name]
    except KeyError as exc:
        raise ToolContractError(f"Tool contract not defined: {tool_name}") from exc


def validate_tool_payload(tool_name: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """Validate a JSON-object-like payload against the registered tool contract."""
    contract = get_tool_contract(tool_name)
    tool_payload = payload or {}
    if not isinstance(tool_payload, dict):
        raise ToolContractError("Tool payload must be a dictionary.")

    for field in contract.required_fields:
        if field not in tool_payload or tool_payload[field] is None:
            raise ToolContractError(f"{field} is required.")

    for field in contract.string_fields:
        if field in tool_payload and tool_payload[field] is not None and not isinstance(tool_payload[field], str):
            raise ToolContractError(f"{field} must be a string.")

    for field in contract.object_fields:
        if field in tool_payload and tool_payload[field] is not None and not isinstance(tool_payload[field], dict):
            raise ToolContractError(f"{field} must be an object.")

    for field in contract.boolean_fields:
        if field in tool_payload and tool_payload[field] is not None and not isinstance(tool_payload[field], bool):
            raise ToolContractError(f"{field} must be a boolean.")

    for field in contract.integer_fields:
        if field in tool_payload and tool_payload[field] is not None and not isinstance(tool_payload[field], int):
            raise ToolContractError(f"{field} must be an integer.")

    return tool_payload
