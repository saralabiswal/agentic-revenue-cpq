from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    intent: str
    messages: list[dict[str, Any]]
    user_input: str
    retrieved_context: list[str]
    tools_output: dict[str, Any]
    final_answer: str
    sf_opportunity_id: str
    selected_products: list[dict[str, Any]]
    opportunity: dict[str, Any]
    recommendation: dict[str, Any]
    pricing: dict[str, Any]
    quote: dict[str, Any]
    persist_quote: bool
    run_steps: list[dict[str, Any]]
    assistant_message: dict[str, Any]
    response: dict[str, Any]
    status: str
