from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class MultimodalType(str, Enum):
    """Supported multimodal content types."""

    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"


class MultimodalStatus(str, Enum):
    """Lifecycle status for multimodal contexts."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, Enum):
    """Allowed analysis modes."""

    FULL = "full"
    OCR = "ocr"
    METADATA_ONLY = "metadata_only"


class MultimodalContextCreate(BaseModel):
    """Payload for creating a multimodal context."""

    content_type: MultimodalType = Field(description="Type of content being created")
    text_content: str | None = Field(
        default=None,
        description="Optional text body for text-based contexts",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata associated with the context",
    )

    @model_validator(mode="after")
    def validate_payload(self) -> "MultimodalContextCreate":
        if self.content_type == MultimodalType.TEXT and not self.text_content:
            raise ValueError("text_content is required when content_type is 'text'")
        return self


class MultimodalContextResponse(BaseModel):
    """Serialized multimodal context."""

    id: str
    content_type: MultimodalType
    status: MultimodalStatus
    original_filename: str | None = None
    text_content: str | None = None
    analysis: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tokens_estimate: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime


class AnalysisRequest(BaseModel):
    """Payload for executing context analysis."""

    analysis_type: AnalysisType = Field(default=AnalysisType.FULL)
    custom_prompt: str | None = Field(
        default=None,
        description="Optional prompt override for full image analysis",
    )


class AnalysisResponse(BaseModel):
    """Result of a multimodal analysis request."""

    context_id: str
    analysis_type: AnalysisType
    status: MultimodalStatus
    result: dict[str, Any] = Field(default_factory=dict)
    tokens_estimate: int = Field(default=0, ge=0)
    analyzed_at: datetime
