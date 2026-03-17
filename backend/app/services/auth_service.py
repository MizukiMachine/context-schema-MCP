from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

from app.config import Settings, get_settings


class AuthService:
    """Service for password hashing and JWT handling."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Hash a plain password."""
        return self._pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Verify a plain password against a hash."""
        return self._pwd_context.verify(plain, hashed)

    def create_access_token(
        self,
        user_id: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed access token."""
        expire_at = datetime.now(timezone.utc) + (
            expires_delta or timedelta(hours=self.settings.jwt_expiration_hours)
        )
        payload = {
            "sub": user_id,
            "exp": expire_at,
            "type": "access",
        }
        return jwt.encode(
            payload,
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )

    def create_refresh_token(self, user_id: str) -> str:
        """Create a signed refresh token."""
        expire_at = datetime.now(timezone.utc) + timedelta(
            days=self.settings.jwt_refresh_expiration_days
        )
        payload = {
            "sub": user_id,
            "exp": expire_at,
            "type": "refresh",
        }
        return jwt.encode(
            payload,
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )

    def verify_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT."""
        payload = jwt.decode(
            token,
            self.settings.jwt_secret,
            algorithms=[self.settings.jwt_algorithm],
        )
        return dict(payload)


def get_auth_service() -> AuthService:
    """Return the authentication service instance."""
    return AuthService()


__all__ = ["AuthService", "PyJWTError", "get_auth_service"]
