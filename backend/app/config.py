from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR / 'context_schema.db'}"
DEFAULT_CORS_ALLOW_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
DEFAULT_CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]
DEFAULT_CORS_ALLOW_HEADERS = [
    "Authorization",
    "Content-Type",
]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "context-schema-mcp-backend"
    database_url: str = Field(default=DEFAULT_DATABASE_URL)
    database_echo: bool = False
    jwt_secret: str = Field(min_length=1)
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_days: int = 7
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash-exp"
    cors_allow_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: DEFAULT_CORS_ALLOW_ORIGINS.copy()
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: DEFAULT_CORS_ALLOW_METHODS.copy()
    )
    cors_allow_headers: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: DEFAULT_CORS_ALLOW_HEADERS.copy()
    )

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        """Reject blank JWT secrets."""
        secret = value.strip()
        if not secret:
            raise ValueError("jwt_secret must not be empty.")
        return secret

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: Any) -> Any:
        """Treat blank optional strings as unset."""
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        return normalized or None

    @field_validator(
        "cors_allow_origins",
        "cors_allow_methods",
        "cors_allow_headers",
        mode="before",
    )
    @classmethod
    def parse_string_list(cls, value: Any) -> Any:
        """Support comma-separated or JSON-array env values for list settings."""
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            return []

        if normalized.startswith("["):
            return json.loads(normalized)

        return [item.strip() for item in normalized.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
