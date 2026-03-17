from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.context_element import ContextElement
from app.models.context_session import ContextSession
from app.models.context_window import ContextWindow
from app.models.user import User
from app.schemas.element import ElementCreate, ElementResponse, ElementUpdate

router = APIRouter(prefix="/elements", tags=["elements"])


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


async def _get_owned_element(
    db: AsyncSession,
    element_id: str,
    user_id: str,
) -> ContextElement | None:
    result = await db.execute(
        select(ContextElement)
        .join(ContextWindow, ContextElement.window_id == ContextWindow.id)
        .join(ContextSession, ContextWindow.session_id == ContextSession.id)
        .where(
            ContextElement.id == element_id,
            ContextSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


@router.post("", response_model=ElementResponse, status_code=status.HTTP_201_CREATED)
async def create_element(
    payload: ElementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContextElement:
    """Create an element under an owned window."""
    window = await _get_owned_window(db, payload.window_id, current_user.id)
    if window is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Window not found")

    element = ContextElement(
        window_id=payload.window_id,
        role=payload.role,
        content=payload.content,
        token_count=payload.token_count,
        metadata_=payload.metadata,
    )
    db.add(element)
    await db.commit()
    await db.refresh(element)
    return element


@router.get("", response_model=list[ElementResponse])
async def list_elements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    window_id: str | None = Query(default=None),
) -> list[ContextElement]:
    """List elements owned by the authenticated user."""
    statement = (
        select(ContextElement)
        .join(ContextWindow, ContextElement.window_id == ContextWindow.id)
        .join(ContextSession, ContextWindow.session_id == ContextSession.id)
        .where(ContextSession.user_id == current_user.id)
        .order_by(ContextElement.created_at.asc())
    )
    if window_id is not None:
        statement = statement.where(ContextElement.window_id == window_id)

    result = await db.execute(statement)
    return list(result.scalars().all())


@router.get("/{element_id}", response_model=ElementResponse)
async def get_element(
    element_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContextElement:
    """Get a single owned element."""
    element = await _get_owned_element(db, element_id, current_user.id)
    if element is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element not found")
    return element


@router.patch("/{element_id}", response_model=ElementResponse)
async def update_element(
    element_id: str,
    payload: ElementUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContextElement:
    """Update a single owned element."""
    element = await _get_owned_element(db, element_id, current_user.id)
    if element is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element not found")

    updates = payload.model_dump(exclude_unset=True)
    if "metadata" in updates:
        updates["metadata_"] = updates.pop("metadata")

    for field, value in updates.items():
        setattr(element, field, value)

    await db.commit()
    await db.refresh(element)
    return element


@router.delete("/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_element(
    element_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete a single owned element."""
    element = await _get_owned_element(db, element_id, current_user.id)
    if element is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element not found")

    await db.delete(element)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
