from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from jwt import PyJWTError
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


async def _parse_login_payload(request: Request) -> UserLogin:
    """Accept JSON or form-encoded login payloads."""
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        payload = {
            "email": form.get("email") or form.get("username"),
            "password": form.get("password"),
        }
        return UserLogin.model_validate(payload)

    body = await request.json()
    return UserLogin.model_validate(body)


def _build_token_response(auth_service: AuthService, user_id: str) -> Token:
    """Create a paired access/refresh response."""
    return Token(
        access_token=auth_service.create_access_token(user_id),
        refresh_token=auth_service.create_refresh_token(user_id),
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """Register a new user and issue tokens."""
    existing_user = await db_session.execute(
        select(User).where(
            or_(
                User.email == user_create.email,
                User.username == user_create.username,
            )
        )
    )
    if existing_user.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    user = User(
        email=user_create.email,
        username=user_create.username,
        hashed_password=auth_service.hash_password(user_create.password),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return _build_token_response(auth_service, user.id)


@router.post("/login", response_model=Token)
async def login(
    credentials: Annotated[UserLogin, Depends(_parse_login_payload)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """Authenticate a user and issue tokens."""
    result = await db_session.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    if user is None or not auth_service.verify_password(
        credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return _build_token_response(auth_service, user.id)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: Annotated[str, Body(embed=True)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """Issue a new access and refresh token pair from a refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = auth_service.verify_token(refresh_token)
    except (PyJWTError, ValueError, TypeError):
        raise credentials_exception from None

    user_id = payload.get("sub")
    if payload.get("type") != "refresh" or not isinstance(user_id, str):
        raise credentials_exception

    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception

    return _build_token_response(auth_service, user_id)


@router.get("/me")
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, Any]:
    """Return the authenticated user's profile."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }
