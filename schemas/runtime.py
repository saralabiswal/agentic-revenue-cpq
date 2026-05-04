"""Pydantic response contracts for runtime profile visibility.

Author: Sarala Biswal
"""

from pydantic import BaseModel


class RuntimeProfileSummary(BaseModel):
    """Display-only runtime profile component labels."""

    runtime_profile: str
    agent_orchestration: str
    llm: str
    embeddings: str
    vector_store: str
    business_store: str
    object_store: str
    secrets: str
    observability: str


class RuntimeProfileResponse(BaseModel):
    """Read-only provider profile response."""

    platform_profile: str
    display_name: str
    agent_orchestrator: str
    llm_provider: str
    embedding_provider: str
    vector_store_provider: str
    business_store_provider: str
    object_store_provider: str
    secrets_provider: str
    observability_provider: str
    editable_in_ui: bool
    summary: RuntimeProfileSummary
    profiles: dict[str, RuntimeProfileSummary]
