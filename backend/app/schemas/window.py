from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
