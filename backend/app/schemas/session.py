from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.context_session import ContextSessionStatus


class SessionCreate(BaseModel):
    """Payload for creating a context session."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: ContextSessionStatus = ContextSessionStatus.ACTIVE


class SessionUpdate(BaseModel):
    """Payload for updating a context session."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ContextSessionStatus | None = None


class SessionResponse(BaseModel):
    """Serialized context session."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    description: str | None
    status: ContextSessionStatus
    created_at: datetime
    updated_at: datetime
