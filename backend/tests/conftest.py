from __future__ import annotations

from collections.abc import AsyncGenerator
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("JWT_SECRET", "test-secret")

import app.models  # noqa: F401
from app.config import Settings
from app.database import Base


@pytest.fixture
def test_settings() -> Settings:
    """Return test-specific settings."""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        database_echo=False,
        jwt_secret="test-secret",
        jwt_expiration_hours=1,
    )


@pytest_asyncio.fixture
async def async_db_session(
    test_settings: Settings,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated in-memory SQLite async session for each test."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=test_settings.database_echo,
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()
