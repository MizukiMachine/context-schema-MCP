from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.context_session import ContextSession
from app.models.user import User
from app.schemas.session import SessionCreate, SessionResponse, SessionUpdate

router = APIRouter(prefix="/sessions", tags=["sessions"])


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


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContextSession:
    """Create a session for the authenticated user."""
    session = ContextSession(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ContextSession]:
    """List sessions owned by the authenticated user."""
    result = await db.execute(
        select(ContextSession)
        .where(ContextSession.user_id == current_user.id)
        .order_by(ContextSession.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContextSession:
    """Get a single owned session."""
    session = await _get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    payload: SessionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContextSession:
    """Update a single owned session."""
    session = await _get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(session, field, value)

    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete a single owned session."""
    session = await _get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    await db.delete(session)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
