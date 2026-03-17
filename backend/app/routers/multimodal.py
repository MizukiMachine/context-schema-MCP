from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.schemas.multimodal import (
    AnalysisRequest,
    AnalysisResponse,
    MultimodalContextCreate,
    MultimodalContextResponse,
)
from app.services.multimodal_processor import (
    MultimodalProcessor,
    get_multimodal_processor,
)

router = APIRouter(prefix="/multimodal", tags=["multimodal"])


@router.post("", response_model=MultimodalContextResponse, status_code=status.HTTP_201_CREATED)
async def create_multimodal_context(
    data: MultimodalContextCreate,
    processor: Annotated[MultimodalProcessor, Depends(get_multimodal_processor)],
) -> MultimodalContextResponse:
    """Create a multimodal context from structured payload."""
    try:
        context = await processor.create_context(data)
        return MultimodalContextResponse(**context)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/upload",
    response_model=MultimodalContextResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    processor: Annotated[MultimodalProcessor, Depends(get_multimodal_processor)],
    file: UploadFile = File(...),
) -> MultimodalContextResponse:
    """Upload an image and create a pending multimodal context."""
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are supported",
        )

    content = await file.read()
    try:
        context = await processor.create_uploaded_context(
            filename=file.filename,
            content_type=file.content_type,
            file_bytes=content,
        )
        return MultimodalContextResponse(**context)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/{context_id}", response_model=MultimodalContextResponse)
async def get_multimodal_context(
    context_id: str,
    processor: Annotated[MultimodalProcessor, Depends(get_multimodal_processor)],
) -> MultimodalContextResponse:
    """Return a stored multimodal context by id."""
    context = await processor.get_context(context_id)
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Context not found")
    return MultimodalContextResponse(**context)


@router.post("/{context_id}/analyze", response_model=AnalysisResponse)
async def analyze_context(
    context_id: str,
    request: AnalysisRequest,
    processor: Annotated[MultimodalProcessor, Depends(get_multimodal_processor)],
) -> AnalysisResponse:
    """Execute analysis for a stored multimodal context."""
    try:
        result = await processor.analyze_context(context_id, request)
        return AnalysisResponse(**result)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Context not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
