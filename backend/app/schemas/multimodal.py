"""Multimodal context API schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MultimodalType(str, Enum):
    """Type of multimodal content."""

    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"


class MultimodalStatus(str, Enum):
    """Status of multimodal context processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MultimodalContextCreate(BaseModel):
    """Request schema for creating multimodal context."""

    content_type: MultimodalType = Field(..., description="Type of multimodal content")
    text_content: str | None = Field(None, description="Text content if type is text")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class MultimodalContextResponse(BaseModel):
    """Response schema for multimodal context."""

    id: str = Field(..., description="Unique context identifier")
    content_type: MultimodalType = Field(..., description="Type of multimodal content")
    status: MultimodalStatus = Field(..., description="Processing status")
    original_filename: str | None = Field(None, description="Original uploaded filename")
    text_content: str | None = Field(None, description="Text content or extracted text")
    analysis: str | None = Field(None, description="AI analysis of the content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Content metadata")
    tokens_estimate: int = Field(default=0, description="Estimated token count")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class AnalysisRequest(BaseModel):
    """Request schema for analysis."""

    analysis_type: str = Field(
        default="full",
        description="Type of analysis: 'full', 'ocr', 'metadata_only'",
    )
    custom_prompt: str | None = Field(
        None,
        description="Custom prompt for AI analysis",
    )


class AnalysisResponse(BaseModel):
    """Response schema for analysis results."""

    context_id: str = Field(..., description="Context identifier")
    analysis_type: str = Field(..., description="Type of analysis performed")
    result: dict[str, Any] = Field(..., description="Analysis results")
    tokens_estimate: int = Field(default=0, description="Estimated tokens used")
    analyzed_at: datetime = Field(..., description="Analysis timestamp")


class UploadResponse(BaseModel):
    """Response schema for file upload."""

    id: str = Field(..., description="Unique context identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="Detected content type")
    size_bytes: int = Field(..., description="File size in bytes")
    status: MultimodalStatus = Field(..., description="Processing status")
    message: str = Field(default="Upload successful", description="Status message")
