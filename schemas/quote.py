from typing import Any

from pydantic import BaseModel, Field


class AccountListResponse(BaseModel):
    accounts: list[dict[str, Any]]


class OpportunityListResponse(BaseModel):
    opportunities: list[dict[str, Any]]


class ActivityListResponse(BaseModel):
    sf_opportunity_id: str | None = None
    activity: list[dict[str, Any]]


class ProductSelection(BaseModel):
    sku: str
    name: str
    category: str | None = None
    quantity: int = Field(default=1, ge=1)
    term_months: int = Field(default=12, ge=1)
    selected: bool = True
    required: bool = False
    billing_model: str | None = None
    reason: str | None = None
    rule_id: str | None = None


class RecommendationRequest(BaseModel):
    sf_opportunity_id: str = "SF-OPP-001"
    message: str = (
        "Recommend NetApp-aligned products for this telecom opportunity "
        "and prepare pricing for sales review."
    )


class RecommendationResponse(BaseModel):
    status: str
    message: str
    opportunity: dict[str, Any]
    products: list[dict[str, Any]]
    pricing: dict[str, Any]
    retrieved_context: list[str]
    run_steps: list[dict[str, Any]]


class PricingRequest(BaseModel):
    sf_opportunity_id: str
    currency: str = "USD"
    products: list[ProductSelection] = Field(min_length=1)


class PricingResponse(BaseModel):
    status: str
    products: list[dict[str, Any]]
    pricing: dict[str, Any]
    run_steps: list[dict[str, Any]]


class QuoteCreateRequest(BaseModel):
    sf_opportunity_id: str
    currency: str = "USD"
    products: list[ProductSelection] = Field(min_length=1)


class QuoteCreateResponse(BaseModel):
    status: str
    message: str
    oracle_quote_id: str
    quote: dict[str, Any]
    products: list[dict[str, Any]]
    pricing: dict[str, Any]
    run_steps: list[dict[str, Any]]


class QuoteHistoryResponse(BaseModel):
    sf_opportunity_id: str
    quotes: list[dict[str, Any]]


class QuoteFinalizeRequest(BaseModel):
    oracle_quote_id: str


class QuoteFinalizeResponse(BaseModel):
    status: str
    quote: dict[str, Any]
    order: dict[str, Any]
