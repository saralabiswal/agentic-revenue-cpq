"""Pydantic request and response contracts for chat endpoints.

Author: Sarala Biswal
"""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat payload submitted by the sales workbench."""
    message: str = Field(min_length=1)
    sf_opportunity_id: str | None = None


class ChatResponse(BaseModel):
    """Chat endpoint response containing the assistant message and quote details."""
    status: str
    message: str
    oracle_quote_id: str
    products: list[dict[str, Any]]
    pricing: dict[str, Any]
