from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import (
    BASE_DIR,
    DEFAULT_CORS_ALLOW_HEADERS,
    DEFAULT_CORS_ALLOW_METHODS,
    DEFAULT_CORS_ALLOW_ORIGINS,
    Settings,
)


def test_settings_load_values_from_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "JWT_SECRET=env-secret",
                "DATABASE_ECHO=true",
                "CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173",
                'CORS_ALLOW_METHODS=["GET","POST"]',
                "CORS_ALLOW_HEADERS=Authorization,Content-Type,X-Trace-Id",
                "GEMINI_API_KEY=",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.jwt_secret == "env-secret"
    assert settings.database_echo is True
    assert settings.cors_allow_origins == DEFAULT_CORS_ALLOW_ORIGINS
    assert settings.cors_allow_methods == ["GET", "POST"]
    assert settings.cors_allow_headers == [
        "Authorization",
        "Content-Type",
        "X-Trace-Id",
    ]
    assert settings.gemini_api_key is None


def test_settings_raise_error_when_required_fields_are_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_apply_defaults() -> None:
    settings = Settings(jwt_secret="default-secret", _env_file=None)

    assert settings.app_name == "context-schema-mcp-backend"
    assert settings.database_url == f"sqlite+aiosqlite:///{BASE_DIR / 'context_schema.db'}"
    assert settings.database_echo is False
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expiration_hours == 24
    assert settings.jwt_refresh_expiration_days == 7
    assert settings.gemini_model == "gemini-2.0-flash-exp"
    assert settings.cors_allow_origins == DEFAULT_CORS_ALLOW_ORIGINS
    assert settings.cors_allow_credentials is True
    assert settings.cors_allow_methods == DEFAULT_CORS_ALLOW_METHODS
    assert settings.cors_allow_headers == DEFAULT_CORS_ALLOW_HEADERS
