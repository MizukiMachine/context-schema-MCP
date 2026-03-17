from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api import api_router
from app.config import get_settings
from app.database import init_db
from app.routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize database schema during application startup."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        lifespan=lifespan,
    )
    app.include_router(auth_router)
    app.include_router(api_router)
    return app


app = create_app()
