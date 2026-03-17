from __future__ import annotations

from datetime import timedelta

import pytest

from app.config import Settings
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service() -> AuthService:
    """Return an AuthService instance with test settings."""
    return AuthService(Settings(jwt_secret="test-secret-key", jwt_expiration_hours=1))


class TestPasswordHashing:
    def test_hash_password(self, auth_service: AuthService) -> None:
        password = "mysecretpassword"
        hashed = auth_service.hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self, auth_service: AuthService) -> None:
        password = "mysecretpassword"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, auth_service: AuthService) -> None:
        password = "mysecretpassword"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password("wrongpassword", hashed) is False


class TestJWTToken:
    def test_create_access_token(self, auth_service: AuthService) -> None:
        user_id = "user-123"
        token = auth_service.create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts

    def test_create_access_token_with_expiry(self, auth_service: AuthService) -> None:
        user_id = "user-123"
        expires = timedelta(minutes=30)
        token = auth_service.create_access_token(user_id, expires_delta=expires)

        payload = auth_service.verify_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_create_refresh_token(self, auth_service: AuthService) -> None:
        user_id = "user-456"
        token = auth_service.create_refresh_token(user_id)

        payload = auth_service.verify_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_verify_token_valid(self, auth_service: AuthService) -> None:
        user_id = "user-789"
        token = auth_service.create_access_token(user_id)

        payload = auth_service.verify_token(token)

        assert payload["sub"] == user_id
        assert "exp" in payload
        assert payload["type"] == "access"

    def test_verify_token_invalid(self, auth_service: AuthService) -> None:
        with pytest.raises(Exception):  # jwt.DecodeError
            auth_service.verify_token("invalid.token.here")

    def test_verify_token_wrong_secret(self, auth_service: AuthService) -> None:
        user_id = "user-123"
        token = auth_service.create_access_token(user_id)

        # Try to verify with different service (different secret)
        other_service = AuthService(Settings(jwt_secret="different-secret", jwt_expiration_hours=1))

        with pytest.raises(Exception):  # jwt.InvalidSignatureError
            other_service.verify_token(token)
