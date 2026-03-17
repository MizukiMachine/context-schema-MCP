"""Unit tests for ContextSession model."""

from __future__ import annotations

import pytest

from app.models.context_session import ContextSession, ContextSessionStatus


class TestContextSessionModel:
    """Tests for ContextSession model."""

    def test_create_session_with_required_fields(self) -> None:
        """Test creating a session with only required fields."""
        session = ContextSession(
            user_id="user-123",
            name="Test Session",
        )

        assert session.user_id == "user-123"
        assert session.name == "Test Session"

    def test_create_session_with_all_fields(self) -> None:
        """Test creating a session with all fields."""
        session = ContextSession(
            user_id="user-456",
            name="Full Session",
            description="A comprehensive test session",
            status=ContextSessionStatus.ACTIVE,
        )

        assert session.user_id == "user-456"
        assert session.name == "Full Session"
        assert session.description == "A comprehensive test session"
        assert session.status == ContextSessionStatus.ACTIVE

    def test_session_status_enum_values(self) -> None:
        """Test ContextSessionStatus enum values."""
        assert ContextSessionStatus.ACTIVE.value == "active"
        assert ContextSessionStatus.ARCHIVED.value == "archived"

    def test_session_default_status(self) -> None:
        """Test default status is ACTIVE."""
        session = ContextSession(
            user_id="user-789",
            name="Default Status Session",
        )

        # Check table column default
        status_column = ContextSession.__table__.c.status
        assert status_column.default.arg == ContextSessionStatus.ACTIVE

    def test_session_table_name(self) -> None:
        """Test that table name is correct."""
        assert ContextSession.__tablename__ == "context_sessions"

    def test_session_user_id_is_indexed(self) -> None:
        """Test that user_id column is indexed."""
        user_id_column = ContextSession.__table__.c.user_id
        assert user_id_column.index is True

    def test_session_name_is_indexed(self) -> None:
        """Test that name column is indexed."""
        name_column = ContextSession.__table__.c.name
        assert name_column.index is True

    def test_session_description_is_nullable(self) -> None:
        """Test that description is nullable."""
        description_column = ContextSession.__table__.c.description
        assert description_column.nullable is True

    def test_session_id_is_uuid_string(self) -> None:
        """Test that session ID is generated as UUID string."""
        session1 = ContextSession(user_id="user-1", name="Session 1")
        session2 = ContextSession(user_id="user-2", name="Session 2")

        # IDs should be different UUIDs
        assert session1.id != session2.id
        # ID should be a 36-character UUID string
        assert len(session1.id) == 36
        assert session1.id.count("-") == 4

    def test_session_archived_status(self) -> None:
        """Test creating an archived session."""
        session = ContextSession(
            user_id="user-archive",
            name="Archived Session",
            status=ContextSessionStatus.ARCHIVED,
        )

        assert session.status == ContextSessionStatus.ARCHIVED

    def test_session_active_status(self) -> None:
        """Test creating an active session."""
        session = ContextSession(
            user_id="user-active",
            name="Active Session",
            status=ContextSessionStatus.ACTIVE,
        )

        assert session.status == ContextSessionStatus.ACTIVE

    def test_session_windows_relationship(self) -> None:
        """Test that session has windows relationship."""
        # Check relationship exists
        assert hasattr(ContextSession, "windows")
        # Check relationship configuration
        relationship = ContextSession.__mapper__.relationships.get("windows")
        assert relationship is not None
        assert relationship.cascade == "all, delete-orphan"

    def test_session_description_text_type(self) -> None:
        """Test that description uses Text type for long content."""
        from sqlalchemy import Text

        description_column = ContextSession.__table__.c.description
        assert isinstance(description_column.type, Text)
