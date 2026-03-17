"""Unit tests for User model."""

from __future__ import annotations

import pytest

from app.models.user import User


class TestUserModel:
    """Tests for User model."""

    def test_create_user_with_required_fields(self) -> None:
        """Test creating a user with only required fields."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_secret",
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_secret"

    def test_create_user_with_all_fields(self) -> None:
        """Test creating a user with all fields."""
        user = User(
            email="full@example.com",
            username="fulluser",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=True,
        )

        assert user.email == "full@example.com"
        assert user.username == "fulluser"
        assert user.hashed_password == "hashed_password"
        assert user.is_active is True
        assert user.is_superuser is True

    def test_user_default_values(self) -> None:
        """Test default values for user fields."""
        user = User(
            email="defaults@example.com",
            username="defaultuser",
            hashed_password="hashed",
        )

        # Check table column defaults
        assert User.__table__.c.is_active.default.arg is True
        assert User.__table__.c.is_superuser.default.arg is False

    def test_user_email_is_unique(self) -> None:
        """Test that email column has unique constraint."""
        email_column = User.__table__.c.email
        assert email_column.unique is True

    def test_user_username_is_unique(self) -> None:
        """Test that username column has unique constraint."""
        username_column = User.__table__.c.username
        assert username_column.unique is True

    def test_user_email_is_indexed(self) -> None:
        """Test that email column is indexed."""
        email_column = User.__table__.c.email
        assert email_column.index is True

    def test_user_username_is_indexed(self) -> None:
        """Test that username column is indexed."""
        username_column = User.__table__.c.username
        assert username_column.index is True

    def test_user_table_name(self) -> None:
        """Test that table name is correct."""
        assert User.__tablename__ == "users"

    def test_user_id_is_uuid_string(self) -> None:
        """Test that user ID is generated as UUID string."""
        user1 = User(
            email="user1@example.com",
            username="user1",
            hashed_password="hash1",
        )
        user2 = User(
            email="user2@example.com",
            username="user2",
            hashed_password="hash2",
        )

        # IDs should be different UUIDs
        assert user1.id != user2.id
        # ID should be a 36-character UUID string
        assert len(user1.id) == 36
        assert user1.id.count("-") == 4

    def test_user_inactive_state(self) -> None:
        """Test creating an inactive user."""
        user = User(
            email="inactive@example.com",
            username="inactive",
            hashed_password="hashed",
            is_active=False,
        )

        assert user.is_active is False

    def test_user_superuser_state(self) -> None:
        """Test creating a superuser."""
        user = User(
            email="admin@example.com",
            username="admin",
            hashed_password="hashed",
            is_superuser=True,
        )

        assert user.is_superuser is True

    def test_user_normal_user_state(self) -> None:
        """Test creating a normal (non-superuser) active user."""
        user = User(
            email="normal@example.com",
            username="normal",
            hashed_password="hashed",
            is_active=True,
            is_superuser=False,
        )

        assert user.is_active is True
        assert user.is_superuser is False
