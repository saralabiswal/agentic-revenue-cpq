from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    sf_opportunity_id: str | None = None


class ChatResponse(BaseModel):
    status: str
    message: str
    oracle_quote_id: str
    products: list[dict[str, Any]]
    pricing: dict[str, Any]
