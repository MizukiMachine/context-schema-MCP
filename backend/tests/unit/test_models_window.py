"""Unit tests for ContextWindow model."""

from __future__ import annotations

import pytest

from app.models.context_window import ContextWindow


class TestContextWindowModel:
    """Tests for ContextWindow model."""

    def test_create_window_with_required_fields(self) -> None:
        """Test creating a window with only required fields."""
        window = ContextWindow(
            session_id="session-123",
            name="Test Window",
            provider="openai",
            model="gpt-4",
            token_limit=4096,
        )

        assert window.session_id == "session-123"
        assert window.name == "Test Window"
        assert window.provider == "openai"
        assert window.model == "gpt-4"
        assert window.token_limit == 4096

    def test_create_window_with_all_fields(self) -> None:
        """Test creating a window with all fields."""
        window = ContextWindow(
            session_id="session-456",
            name="Full Window",
            provider="anthropic",
            model="claude-3-opus",
            system_prompt="You are a helpful assistant.",
            token_limit=8192,
        )

        assert window.session_id == "session-456"
        assert window.name == "Full Window"
        assert window.provider == "anthropic"
        assert window.model == "claude-3-opus"
        assert window.system_prompt == "You are a helpful assistant."
        assert window.token_limit == 8192

    def test_window_table_name(self) -> None:
        """Test that table name is correct."""
        assert ContextWindow.__tablename__ == "context_windows"

    def test_window_session_id_is_indexed(self) -> None:
        """Test that session_id column is indexed."""
        session_id_column = ContextWindow.__table__.c.session_id
        assert session_id_column.index is True

    def test_window_name_is_indexed(self) -> None:
        """Test that name column is indexed."""
        name_column = ContextWindow.__table__.c.name
        assert name_column.index is True

    def test_window_provider_is_indexed(self) -> None:
        """Test that provider column is indexed."""
        provider_column = ContextWindow.__table__.c.provider
        assert provider_column.index is True

    def test_window_session_id_foreign_key(self) -> None:
        """Test that session_id has foreign key to context_sessions."""
        session_id_column = ContextWindow.__table__.c.session_id
        foreign_keys = list(session_id_column.foreign_keys)
        assert len(foreign_keys) == 1
        fk = foreign_keys[0]
        assert fk.column.table.name == "context_sessions"
        assert fk.column.name == "id"

    def test_window_session_id_cascade_delete(self) -> None:
        """Test that foreign key has CASCADE delete."""
        session_id_column = ContextWindow.__table__.c.session_id
        foreign_keys = list(session_id_column.foreign_keys)
        fk = foreign_keys[0]
        assert fk.ondelete == "CASCADE"

    def test_window_system_prompt_is_nullable(self) -> None:
        """Test that system_prompt is nullable."""
        system_prompt_column = ContextWindow.__table__.c.system_prompt
        assert system_prompt_column.nullable is True

    def test_window_system_prompt_text_type(self) -> None:
        """Test that system_prompt uses Text type for long content."""
        from sqlalchemy import Text

        system_prompt_column = ContextWindow.__table__.c.system_prompt
        assert isinstance(system_prompt_column.type, Text)

    def test_window_session_relationship(self) -> None:
        """Test that window has session relationship."""
        assert hasattr(ContextWindow, "session")
        relationship = ContextWindow.__mapper__.relationships.get("session")
        assert relationship is not None

    def test_window_elements_relationship(self) -> None:
        """Test that window has elements relationship with cascade delete."""
        relationship = ContextWindow.__mapper__.relationships.get("elements")
        assert relationship is not None
        # Cascade options format may vary - check it contains the expected values
        cascade_str = str(relationship.cascade).lower()
        assert "delete" in cascade_str
        assert "delete-orphan" in cascade_str

    def test_window_id_is_uuid_string(self) -> None:
        """Test that window ID column is configured as UUID string."""
        # Note: SQLAlchemy default only applies when persisted to DB
        # Check column configuration instead
        id_column = ContextWindow.__table__.c.id
        assert id_column.primary_key is True
        # The default is a lambda that returns UUID string
        assert callable(id_column.default.arg)

    def test_window_different_providers(self) -> None:
        """Test creating windows with different providers."""
        providers = ["openai", "anthropic", "google", "local"]

        for provider in providers:
            window = ContextWindow(
                session_id=f"session-{provider}",
                name=f"Window {provider}",
                provider=provider,
                model=f"model-{provider}",
                token_limit=4096,
            )
            assert window.provider == provider

    def test_window_token_limit_variations(self) -> None:
        """Test windows with different token limits."""
        token_limits = [512, 1024, 2048, 4096, 8192, 16384, 32768, 128000]

        for limit in token_limits:
            window = ContextWindow(
                session_id="session-tokens",
                name=f"Window {limit}",
                provider="openai",
                model="gpt-4",
                token_limit=limit,
            )
            assert window.token_limit == limit

    def test_window_nullable_system_prompt(self) -> None:
        """Test creating window without system prompt."""
        window = ContextWindow(
            session_id="session-no-prompt",
            name="No Prompt Window",
            provider="openai",
            model="gpt-4",
            token_limit=4096,
        )

        assert window.system_prompt is None
