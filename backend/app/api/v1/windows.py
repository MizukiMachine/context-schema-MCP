from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.context_session import ContextSession
from app.models.context_window import ContextWindow
from app.models.user import User
from app.schemas.window import WindowCreate, WindowResponse, WindowUpdate

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
