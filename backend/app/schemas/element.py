from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.context_element import ContextElementRole


class ElementCreate(BaseModel):
    """Payload for creating a context element."""

    window_id: str
    role: ContextElementRole
    content: str = Field(min_length=1)
    token_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ElementUpdate(BaseModel):
    """Payload for updating a context element."""

    role: ContextElementRole | None = None
    content: str | None = Field(default=None, min_length=1)
    token_count: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] | None = None


class ElementResponse(BaseModel):
    """Serialized context element."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    window_id: str
    role: ContextElementRole
    content: str
    token_count: int
    metadata: dict[str, Any] = Field(validation_alias="metadata_", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
