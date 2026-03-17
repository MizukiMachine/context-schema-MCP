from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.context_element import ContextElementRole
from app.services.context_optimizer import OptimizationType


class WindowCreate(BaseModel):
    """Payload for creating a context window."""

    session_id: str
    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=255)
    system_prompt: str | None = None
    token_limit: int = Field(ge=1)


class WindowUpdate(BaseModel):
    """Payload for updating a context window."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=255)
    system_prompt: str | None = None
    token_limit: int | None = Field(default=None, ge=1)


class WindowResponse(BaseModel):
    """Serialized context window."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    name: str
    provider: str
    model: str
    system_prompt: str | None
    token_limit: int
    created_at: datetime
    updated_at: datetime


class WindowOptimizeRequest(BaseModel):
    """Payload for applying a specific optimization strategy."""

    optimization_type: OptimizationType
    params: dict[str, Any] = Field(default_factory=dict)


class WindowAutoOptimizeRequest(BaseModel):
    """Payload for selecting the best optimization strategy automatically."""

    params: dict[str, Any] = Field(default_factory=dict)


class OptimizationElementSnapshot(BaseModel):
    """Serializable snapshot for before/after optimization comparisons."""

    role: ContextElementRole
    content: str
    token_count: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WindowOptimizationResponse(BaseModel):
    """Optimization result for a context window."""

    strategy_used: OptimizationType
    token_savings: int = Field(ge=0)
    token_reduction_ratio: float = Field(ge=0.0)
    quality_improvement: float
    original_token_count: int = Field(ge=0)
    optimized_token_count: int = Field(ge=0)
    original_elements: list[OptimizationElementSnapshot]
    optimized_elements: list[OptimizationElementSnapshot]
