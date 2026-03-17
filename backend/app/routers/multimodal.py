"""Multimodal context API router.

Provides endpoints for uploading, managing, and analyzing multimodal content.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.multimodal import (
    AnalysisRequest,
    AnalysisResponse,
    MultimodalContextCreate,
    MultimodalContextResponse,
    MultimodalStatus,
    MultimodalType,
    UploadResponse,
)
from app.services.multimodal_processor import MultimodalProcessor

router = APIRouter(prefix="/multimodal", tags=["multimodal"])

# In-memory storage for demo purposes
# In production, this would use a database
_contexts: dict[str, dict] = {}


def _get_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


@router.post("", response_model=MultimodalContextResponse)
async def create_multimodal_context(data: MultimodalContextCreate) -> MultimodalContextResponse:
    """
    Create a new multimodal context.

    Use this endpoint to create a text-based context that can later be analyzed.
    """
    context_id = str(uuid.uuid4())
    now = _get_timestamp()

    context = {
        "id": context_id,
        "content_type": data.content_type,
        "status": MultimodalStatus.COMPLETED,
        "original_filename": None,
        "text_content": data.text_content,
        "analysis": None,
        "metadata": data.metadata or {},
        "tokens_estimate": len(data.text_content or "") // 4,
        "created_at": now,
        "updated_at": now,
    }

    _contexts[context_id] = context
    return MultimodalContextResponse(**context)


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload an image file for processing.

    Accepts image files (PNG, JPEG, GIF, WebP).
    The image will be processed and metadata extracted automatically.
    """
    # Validate content type
    allowed_types = {"image/png", "image/jpeg", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
            f"Allowed types: {', '.join(allowed_types)}",
        )

    # Read file content
    content = await file.read()

    # Create context entry
    context_id = str(uuid.uuid4())
    now = _get_timestamp()

    try:
        # Get basic metadata without AI analysis
        processor = MultimodalProcessor()
        metadata = processor.get_image_metadata(content)

        context = {
            "id": context_id,
            "content_type": MultimodalType.IMAGE,
            "status": MultimodalStatus.PENDING,
            "original_filename": file.filename,
            "text_content": None,
            "analysis": None,
            "metadata": metadata,
            "tokens_estimate": 0,
            "created_at": now,
            "updated_at": now,
            "_raw_data": content,  # Store raw data for later analysis
        }

        _contexts[context_id] = context

        return UploadResponse(
            id=context_id,
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            status=MultimodalStatus.PENDING,
            message="Upload successful. Use /multimodal/{id}/analyze to analyze.",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e}") from e


@router.get("/{context_id}", response_model=MultimodalContextResponse)
async def get_multimodal_context(context_id: str) -> MultimodalContextResponse:
    """
    Get multimodal context by ID.

    Returns the context details including metadata and any analysis results.
    """
    if context_id not in _contexts:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")

    context = _contexts[context_id].copy()
    # Remove internal field before returning
    context.pop("_raw_data", None)

    return MultimodalContextResponse(**context)


@router.post("/{context_id}/analyze", response_model=AnalysisResponse)
async def analyze_context(
    context_id: str,
    request: AnalysisRequest,
) -> AnalysisResponse:
    """
    Analyze multimodal context using AI.

    Triggers AI analysis on the uploaded content.
    Analysis types:
    - 'full': Complete analysis including AI description
    - 'ocr': Text extraction only
    - 'metadata_only': Just return existing metadata
    """
    if context_id not in _contexts:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")

    context = _contexts[context_id]
    now = _get_timestamp()

    # Update status
    context["status"] = MultimodalStatus.PROCESSING
    context["updated_at"] = now

    try:
        processor = MultimodalProcessor()
        result = {}
        tokens_estimate = 0

        if request.analysis_type == "metadata_only":
            # Just return existing metadata
            result = context.get("metadata", {})
            tokens_estimate = 0

        elif request.analysis_type == "ocr":
            # Extract text using OCR
            raw_data = context.get("_raw_data")
            if raw_data:
                extracted_text = await processor.extract_text_ocr(raw_data)
                result = {"extracted_text": extracted_text}
                tokens_estimate = len(extracted_text) // 4
                context["text_content"] = extracted_text
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No image data available for OCR",
                )

        else:  # 'full' analysis
            raw_data = context.get("_raw_data")
            if raw_data:
                analysis_result = await processor.process_image(raw_data)
                result = analysis_result
                tokens_estimate = analysis_result.get("tokens_estimate", 0)
                context["analysis"] = analysis_result.get("analysis")
                context["metadata"].update(
                    {
                        k: v
                        for k, v in analysis_result.items()
                        if k not in ("analysis", "tokens_estimate")
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No image data available for analysis",
                )

        # Update context status
        context["status"] = MultimodalStatus.COMPLETED
        context["tokens_estimate"] = tokens_estimate
        context["updated_at"] = now

        return AnalysisResponse(
            context_id=context_id,
            analysis_type=request.analysis_type,
            result=result,
            tokens_estimate=tokens_estimate,
            analyzed_at=now,
        )

    except HTTPException:
        raise
    except Exception as e:
        context["status"] = MultimodalStatus.FAILED
        context["updated_at"] = now
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e
