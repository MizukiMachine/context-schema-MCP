from __future__ import annotations

from typing import Any
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.context_element import ContextElement
from app.models.context_session import ContextSession
from app.models.context_window import ContextWindow
from app.models.user import User
from app.services.context_analyzer import AnalysisResult, ContextAnalyzer, get_context_analyzer
from app.services.context_optimizer import (
    ContextOptimizer,
    OptimizationResult,
    get_context_optimizer,
)
from app.schemas.window import (
    OptimizationElementSnapshot,
    WindowAutoOptimizeRequest,
    WindowCreate,
    WindowOptimizationResponse,
    WindowOptimizeRequest,
    WindowResponse,
    WindowUpdate,
)

router = APIRouter(prefix="/windows", tags=["windows"])


async def _get_owned_session(
    db: AsyncSession,
    session_id: str,
    user_id: str,
) -> ContextSession | None:
    result = await db.execute(
        select(ContextSession).where(
            ContextSession.id == session_id,
            ContextSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def _get_owned_window(
    db: AsyncSession,
    window_id: str,
    user_id: str,
) -> ContextWindow | None:
    result = await db.execute(
        select(ContextWindow)
        .join(ContextSession, ContextWindow.session_id == ContextSession.id)
        .where(
            ContextWindow.id == window_id,
            ContextSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


def _serialize_optimization_element(element: ContextElement) -> OptimizationElementSnapshot:
    return OptimizationElementSnapshot(
        role=element.role,
        content=element.content,
        token_count=element.token_count,
        metadata=dict(element.metadata_),
    )


def _serialize_optimization_result(result: OptimizationResult) -> WindowOptimizationResponse:
    original_token_count = sum(element.token_count for element in result.original_elements)
    optimized_token_count = sum(element.token_count for element in result.optimized_elements)
    token_reduction_ratio = 0.0
    if original_token_count > 0:
        token_reduction_ratio = result.token_savings / original_token_count

    return WindowOptimizationResponse(
        strategy_used=result.strategy_used,
        token_savings=result.token_savings,
        token_reduction_ratio=round(token_reduction_ratio, 3),
        quality_improvement=result.quality_improvement,
        original_token_count=original_token_count,
        optimized_token_count=optimized_token_count,
        original_elements=[
            _serialize_optimization_element(element) for element in result.original_elements
        ],
        optimized_elements=[
            _serialize_optimization_element(element) for element in result.optimized_elements
        ],
    )


def _merge_optimization_params(
    *,
    payload_params: dict[str, Any],
    window: ContextWindow,
) -> dict[str, Any]:
    merged = dict(payload_params)
    merged.setdefault("token_limit", window.token_limit)
    return merged


@router.post("", response_model=WindowResponse, status_code=status.HTTP_201_CREATED)
async def create_window(
    payload: WindowCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContextWindow:
    """Create a window under an owned session."""
    session = await _get_owned_session(db, payload.session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    window = ContextWindow(**payload.model_dump())
    db.add(window)
    await db.commit()
    await db.refresh(window)
    return window


@router.get("", response_model=list[WindowResponse])
async def list_windows(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    session_id: str | None = Query(default=None),
) -> list[ContextWindow]:
    """List windows owned by the authenticated user."""
    statement = (
        select(ContextWindow)
        .join(ContextSession, ContextWindow.session_id == ContextSession.id)
        .where(ContextSession.user_id == current_user.id)
        .order_by(ContextWindow.created_at.desc())
    )
    if session_id is not None:
        statement = statement.where(ContextWindow.session_id == session_id)

    result = await db.execute(statement)
    return list(result.scalars().all())


@router.get("/{window_id}", response_model=WindowResponse)
async def get_window(
    window_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContextWindow:
    """Get a single owned window."""
    window = await _get_owned_window(db, window_id, current_user.id)
    if window is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Window not found")
    return window


@router.patch("/{window_id}", response_model=WindowResponse)
async def update_window(
    window_id: str,
    payload: WindowUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContextWindow:
    """Update a single owned window."""
    window = await _get_owned_window(db, window_id, current_user.id)
    if window is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Window not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(window, field, value)

    await db.commit()
    await db.refresh(window)
    return window


@router.delete("/{window_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_window(
    window_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete a single owned window."""
    window = await _get_owned_window(db, window_id, current_user.id)
    if window is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Window not found")

    await db.delete(window)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{window_id}/analyze", response_model=AnalysisResult)
async def analyze_window(
    window_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    analyzer: Annotated[ContextAnalyzer, Depends(get_context_analyzer)],
) -> AnalysisResult:
    """Analyze the quality of a single owned window."""
    window = await _get_owned_window(db, window_id, current_user.id)
    if window is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Window not found")

    result = await db.execute(
        select(ContextElement)
        .where(ContextElement.window_id == window_id)
        .order_by(ContextElement.created_at.asc())
    )
    elements = list(result.scalars().all())
    return await analyzer.analyze(elements)


@router.post("/{window_id}/optimize", response_model=WindowOptimizationResponse)
async def optimize_window(
    window_id: str,
    payload: WindowOptimizeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    optimizer: Annotated[ContextOptimizer, Depends(get_context_optimizer)],
) -> WindowOptimizationResponse:
    """Optimize a single owned window with an explicit strategy."""
    window = await _get_owned_window(db, window_id, current_user.id)
    if window is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Window not found")

    result = await db.execute(
        select(ContextElement)
        .where(ContextElement.window_id == window_id)
        .order_by(ContextElement.created_at.asc())
    )
    elements = list(result.scalars().all())
    optimization_result = await optimizer.optimize(
        elements,
        payload.optimization_type,
        _merge_optimization_params(payload_params=payload.params, window=window),
    )
    return _serialize_optimization_result(optimization_result)


@router.post("/{window_id}/auto-optimize", response_model=WindowOptimizationResponse)
async def auto_optimize_window(
    window_id: str,
    payload: WindowAutoOptimizeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    optimizer: Annotated[ContextOptimizer, Depends(get_context_optimizer)],
) -> WindowOptimizationResponse:
    """Automatically choose the best optimization strategy for a single owned window."""
    window = await _get_owned_window(db, window_id, current_user.id)
    if window is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Window not found")

    result = await db.execute(
        select(ContextElement)
        .where(ContextElement.window_id == window_id)
        .order_by(ContextElement.created_at.asc())
    )
    elements = list(result.scalars().all())
    optimization_result = await optimizer.auto_optimize(
        elements,
        _merge_optimization_params(payload_params=payload.params, window=window),
    )
    return _serialize_optimization_result(optimization_result)
