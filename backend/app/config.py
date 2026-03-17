from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "context-schema-mcp-backend"
    database_url: str = Field(
        default_factory=lambda: (
            f"sqlite+aiosqlite:///{Path(__file__).resolve().parents[2] / 'context_schema.db'}"
        )
    )
    database_echo: bool = False
    jwt_secret: str = "change-me-in-production"
    jwt_expiration_hours: int = 24


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
