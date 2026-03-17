from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.elements import router as elements_router
from app.api.v1.health import router as health_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.windows import router as windows_router

router = APIRouter()
router.include_router(health_router)
router.include_router(sessions_router)
router.include_router(windows_router)
router.include_router(elements_router)

versioned_router = APIRouter(prefix="/api/v1")
versioned_router.include_router(health_router)
versioned_router.include_router(sessions_router)
versioned_router.include_router(windows_router)
versioned_router.include_router(elements_router)

router.include_router(versioned_router)
