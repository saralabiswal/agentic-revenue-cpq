"""Typed state contract passed between LangGraph agent nodes.

Author: Sarala Biswal
"""

from typing import Any, TypedDict

# LangGraph state flow:
# - Nodes receive this dictionary-like state.
# - Each node returns only the keys it adds or updates.
# - LangGraph merges those partial updates into the next node's input.


class AgentState(TypedDict, total=False):
    """Shared LangGraph state containing user input, business records, tool outputs, and responses."""
    # Request/input fields.
    intent: str
    messages: list[dict[str, Any]]
    user_input: str
    sf_opportunity_id: str
    selected_products: list[dict[str, Any]]
    persist_quote: bool

    # Tool and integration outputs accumulated by graph nodes.
    retrieved_context: list[str]
    tools_output: dict[str, Any]
    opportunity: dict[str, Any]
    recommendation: dict[str, Any]
    pricing: dict[str, Any]
    quote: dict[str, Any]

    # Response/audit fields returned to FastAPI and the frontend.
    run_steps: list[dict[str, Any]]
    assistant_message: dict[str, Any]
    final_answer: str
    response: dict[str, Any]
    status: str
