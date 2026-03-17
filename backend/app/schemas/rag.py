"""RAG Context Management API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Request schema for adding a document."""

    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] | None = Field(None, description="Optional metadata")
    source: str | None = Field(None, description="Source identifier")


    tags: list[str] | None = Field(None, description="Tags for categorization")


class DocumentResponse(BaseModel):
    """Response schema for a document."""

    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    tokens_estimate: int = Field(default=0, description="Estimated token count")


class SearchRequest(BaseModel):
    """Request schema for semantic search."""

    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, ge=1, description="Number of results to return")
    min_score: float = Field(default=0.0, ge=1.0, description="Minimum similarity score")
    include_content: bool = Field(default=True, description="Include document content in results")


class SearchResponse(BaseModel):
    """Response schema for search results."""

    query: str = Field(..., description="Original search query")
    results: list[dict[str, Any]] = Field(default_factory=list, description="Search results")
    total: int = Field(default=0, description="Total results count")
    built_context: dict[str, Any] | None = Field(None, description="Built context from results")


