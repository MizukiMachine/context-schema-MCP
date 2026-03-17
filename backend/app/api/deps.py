from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_current_active_user
from app.models.user import User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for API routes."""
    async for session in get_db_session():
        yield session


async def get_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Provide the authenticated active user for API routes."""
    return current_user
