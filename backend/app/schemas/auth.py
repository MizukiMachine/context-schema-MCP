from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: str
    username: str
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""

    email: str
    password: str


class Token(BaseModel):
    """Schema for issued tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT payload parsing."""

    model_config = ConfigDict(extra="ignore")

    sub: str
    exp: int
