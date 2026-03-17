"""Unit tests for ContextElement model."""

from __future__ import annotations

import pytest

from app.models.context_element import ContextElement, ContextElementRole


class TestContextElementModel:
    """Tests for ContextElement model."""

    def test_create_element_with_required_fields(self) -> None:
        """Test creating an element with only required fields."""
        element = ContextElement(
            window_id="window-123",
            role=ContextElementRole.USER,
            content="Hello, world!",
        )

        assert element.window_id == "window-123"
        assert element.role == ContextElementRole.USER
        assert element.content == "Hello, world!"
        assert element.token_count == 0  # default

    def test_create_element_with_all_fields(self) -> None:
        """Test creating an element with all fields."""
        element = ContextElement(
            window_id="window-456",
            role=ContextElementRole.ASSISTANT,
            content="Hi there!",
            token_count=5,
            metadata_={"key": "value", "count": 42},
        )

        assert element.window_id == "window-456"
        assert element.role == ContextElementRole.ASSISTANT
        assert element.content == "Hi there!"
        assert element.token_count == 5
        assert element.metadata_ == {"key": "value", "count": 42}

    def test_element_role_enum_values(self) -> None:
        """Test ContextElementRole enum values."""
        assert ContextElementRole.SYSTEM.value == "system"
        assert ContextElementRole.USER.value == "user"
        assert ContextElementRole.ASSISTANT.value == "assistant"
        assert ContextElementRole.TOOL.value == "tool"

    def test_element_table_name(self) -> None:
        """Test that table name is correct."""
        assert ContextElement.__tablename__ == "context_elements"

    def test_element_window_id_is_indexed(self) -> None:
        """Test that window_id column is indexed."""
        window_id_column = ContextElement.__table__.c.window_id
        assert window_id_column.index is True

    def test_element_role_is_indexed(self) -> None:
        """Test that role column is indexed."""
        role_column = ContextElement.__table__.c.role
        assert role_column.index is True

    def test_element_window_id_foreign_key(self) -> None:
        """Test that window_id has foreign key to context_windows."""
        window_id_column = ContextElement.__table__.c.window_id
        foreign_keys = list(window_id_column.foreign_keys)
        assert len(foreign_keys) == 1
        fk = foreign_keys[0]
        assert fk.column.table.name == "context_windows"
        assert fk.column.name == "id"

    def test_element_window_id_cascade_delete(self) -> None:
        """Test that foreign key has CASCADE delete."""
        window_id_column = ContextElement.__table__.c.window_id
        foreign_keys = list(window_id_column.foreign_keys)
        fk = foreign_keys[0]
        assert fk.ondelete == "CASCADE"

    def test_element_token_count_default(self) -> None:
        """Test that token_count default is 0."""
        token_count_column = ContextElement.__table__.c.token_count
        assert token_count_column.default.arg == 0

    def test_element_metadata_default(self) -> None:
        """Test that metadata defaults to empty dict."""
        element = ContextElement(
            window_id="window-meta",
            role=ContextElementRole.USER,
            content="Test",
        )

        assert element.metadata_ == {}

    def test_element_metadata_column_name(self) -> None:
        """Test that metadata_ maps to 'metadata' column."""
        metadata_column = ContextElement.__table__.c.metadata
        assert metadata_column is not None

    def test_element_window_relationship(self) -> None:
        """Test that element has window relationship."""
        assert hasattr(ContextElement, "window")
        relationship = ContextElement.__mapper__.relationships.get("window")
        assert relationship is not None

    def test_element_all_roles(self) -> None:
        """Test creating elements with all roles."""
        roles_content = [
            (ContextElementRole.SYSTEM, "System message"),
            (ContextElementRole.USER, "User message"),
            (ContextElementRole.ASSISTANT, "Assistant message"),
            (ContextElementRole.TOOL, "Tool response"),
        ]

        for role, content in roles_content:
            element = ContextElement(
                window_id="window-roles",
                role=role,
                content=content,
            )
            assert element.role == role
            assert element.content == content

    def test_element_content_text_type(self) -> None:
        """Test that content uses Text type for long content."""
        from sqlalchemy import Text

        content_column = ContextElement.__table__.c.content
        assert isinstance(content_column.type, Text)

    def test_element_id_is_uuid_string(self) -> None:
        """Test that element ID is generated as UUID string."""
        element1 = ContextElement(
            window_id="window-1",
            role=ContextElementRole.USER,
            content="First",
        )
        element2 = ContextElement(
            window_id="window-2",
            role=ContextElementRole.USER,
            content="Second",
        )

        # IDs should be different UUIDs
        assert element1.id != element2.id
        # ID should be a 36-character UUID string
        assert len(element1.id) == 36
        assert element1.id.count("-") == 4

    def test_element_long_content(self) -> None:
        """Test element with long content."""
        long_content = "x" * 10000
        element = ContextElement(
            window_id="window-long",
            role=ContextElementRole.USER,
            content=long_content,
            token_count=2500,
        )

        assert element.content == long_content
        assert element.token_count == 2500

    def test_element_complex_metadata(self) -> None:
        """Test element with complex metadata."""
        complex_metadata = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "string": "test",
            "number": 42,
            "boolean": True,
        }
        element = ContextElement(
            window_id="window-complex",
            role=ContextElementRole.ASSISTANT,
            content="Complex metadata test",
            metadata_=complex_metadata,
        )

        assert element.metadata_ == complex_metadata
        assert element.metadata_["nested"]["key"] == "value"
        assert element.metadata_["list"] == [1, 2, 3]

    def test_element_role_enum_string_conversion(self) -> None:
        """Test that role enum can be converted to string."""
        for role in ContextElementRole:
            assert str(role.value) in ["system", "user", "assistant", "tool"]
