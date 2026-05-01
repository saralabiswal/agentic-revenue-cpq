"""Pydantic request and response contracts for quote orchestration APIs.

Author: Sarala Biswal
"""

from typing import Any

from pydantic import BaseModel, Field


class AccountListResponse(BaseModel):
    """Response wrapper for Salesforce account list results."""
    accounts: list[dict[str, Any]]


class OpportunityListResponse(BaseModel):
    """Response wrapper for Salesforce opportunity list results."""
    opportunities: list[dict[str, Any]]


class ActivityListResponse(BaseModel):
    """Response wrapper for timeline activity events."""
    sf_opportunity_id: str | None = None
    activity: list[dict[str, Any]]


class ProductSelection(BaseModel):
    """Selected product payload used for pricing and quote creation."""
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
    """Request to recommend products and estimate pricing for an opportunity."""
    sf_opportunity_id: str = "SF-OPP-001"
    message: str = (
        "Recommend NetApp-aligned products for this telecom opportunity "
        "and prepare pricing for sales review."
    )


class RecommendationResponse(BaseModel):
    """Recommendation result returned for sales rep review."""
    status: str
    message: str
    opportunity: dict[str, Any]
    products: list[dict[str, Any]]
    pricing: dict[str, Any]
    retrieved_context: list[str]
    run_steps: list[dict[str, Any]]


class PricingRequest(BaseModel):
    """Request to reprice a selected set of products."""
    sf_opportunity_id: str
    currency: str = "USD"
    products: list[ProductSelection] = Field(min_length=1)


class PricingResponse(BaseModel):
    """Pricing result returned after CPQ calculation."""
    status: str
    products: list[dict[str, Any]]
    pricing: dict[str, Any]
    run_steps: list[dict[str, Any]]


class QuoteCreateRequest(BaseModel):
    """Request to create a draft CPQ quote from selected products."""
    sf_opportunity_id: str
    currency: str = "USD"
    products: list[ProductSelection] = Field(min_length=1)


class QuoteCreateResponse(BaseModel):
    """Quote creation response with persisted quote and run trace details."""
    status: str
    message: str
    oracle_quote_id: str
    quote: dict[str, Any]
    products: list[dict[str, Any]]
    pricing: dict[str, Any]
    run_steps: list[dict[str, Any]]


class QuoteHistoryResponse(BaseModel):
    """Response wrapper for quote history attached to an opportunity."""
    sf_opportunity_id: str
    quotes: list[dict[str, Any]]


class QuoteFinalizeRequest(BaseModel):
    """Request to accept a quote and place an order."""
    oracle_quote_id: str


class QuoteFinalizeResponse(BaseModel):
    """Finalization response containing the accepted quote and placed order."""
    status: str
    quote: dict[str, Any]
    order: dict[str, Any]
