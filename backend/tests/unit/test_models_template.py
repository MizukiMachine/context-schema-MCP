"""Unit tests for PromptTemplate model."""

from __future__ import annotations

import pytest

from app.models.prompt_template import (
    PromptTemplate,
    TemplateType,
    extract_variables,
    _sync_prompt_template_variables,
)


class TestExtractVariables:
    """Tests for extract_variables function."""

    def test_extract_single_variable(self) -> None:
        """Test extracting a single variable."""
        template = "Hello {name}!"
        assert extract_variables(template) == ["name"]

    def test_extract_multiple_variables(self) -> None:
        """Test extracting multiple variables."""
        template = "Hello {name}, you have {count} messages from {sender}."
        assert extract_variables(template) == ["name", "count", "sender"]

    def test_extract_with_format_specifier(self) -> None:
        """Test extracting variables with format specifiers."""
        template = "Price: {price:.2f}, debug: {item!r}, padded: {code:>8}"
        assert extract_variables(template) == ["price", "item", "code"]

    def test_extract_nested_variables(self) -> None:
        """Test extracting nested attribute access."""
        template = "User: {user.profile.name}, first item: {items[0].title}"
        assert extract_variables(template) == ["user", "items"]

    def test_extract_empty_template(self) -> None:
        """Test extracting from empty template."""
        assert extract_variables("") == []

    def test_extract_no_variables(self) -> None:
        """Test template with no variables."""
        template = "This is a plain text template with no variables."
        assert extract_variables(template) == []

    def test_extract_duplicate_variables(self) -> None:
        """Test that duplicate variables are deduplicated."""
        template = "Hello {name}, goodbye {name}!"
        assert extract_variables(template) == ["name"]

    def test_extract_mixed_format_and_nested(self) -> None:
        """Test mixed format specifiers and nested access."""
        template = "{user.name!r} has {count:d} items"
        assert extract_variables(template) == ["user", "count"]

    def test_extract_complex_nested(self) -> None:
        """Test complex nested access patterns."""
        template = "First: {data.results[0].id}, Second: {config.settings.theme}"
        assert extract_variables(template) == ["data", "config"]


class TestPromptTemplateModel:
    """Tests for PromptTemplate model."""

    def test_create_template_with_required_fields(self) -> None:
        """Test creating a template with only required fields."""
        template = PromptTemplate(
            name="Greeting",
            template="Hello {name}!",
            category="general",
        )

        assert template.name == "Greeting"
        assert template.template == "Hello {name}!"
        assert template.category == "general"

    def test_create_template_with_all_fields(self) -> None:
        """Test creating a template with all fields."""
        template = PromptTemplate(
            name="Email Template",
            description="Professional email template",
            template="Dear {recipient},\n\n{body}\n\nBest regards",
            type=TemplateType.CHAT,
            category="business",
            tags=["email", "professional"],
            usage_count=100,
            quality_score=0.95,
            created_by="user-123",
            is_public=True,
        )

        assert template.name == "Email Template"
        assert template.description == "Professional email template"
        assert template.type == TemplateType.CHAT
        assert template.category == "business"
        assert template.tags == ["email", "professional"]
        assert template.usage_count == 100
        assert template.quality_score == 0.95
        assert template.created_by == "user-123"
        assert template.is_public is True

    def test_template_type_enum_values(self) -> None:
        """Test TemplateType enum values."""
        assert TemplateType.COMPLETION.value == "completion"
        assert TemplateType.CHAT.value == "chat"
        assert TemplateType.INSTRUCT.value == "instruct"
        assert TemplateType.FEWSHOT.value == "fewshot"
        assert TemplateType.CHAIN_OF_THOUGHT.value == "chain_of_thought"
        assert TemplateType.ROLEPLAY.value == "roleplay"

    def test_template_default_values(self) -> None:
        """Test default values for template fields."""
        template = PromptTemplate(
            name="Default Template",
            template="No variables",
            category="test",
        )

        # Check table column defaults
        assert PromptTemplate.__table__.c.type.default.arg is TemplateType.COMPLETION
        assert PromptTemplate.__table__.c.usage_count.default.arg == 0
        assert PromptTemplate.__table__.c.quality_score.default.arg == 0.0
        assert PromptTemplate.__table__.c.is_public.default.arg is False

    def test_template_table_name(self) -> None:
        """Test that table name is correct."""
        assert PromptTemplate.__tablename__ == "prompt_templates"

    def test_template_name_is_indexed(self) -> None:
        """Test that name column is indexed."""
        name_column = PromptTemplate.__table__.c.name
        assert name_column.index is True

    def test_template_category_is_indexed(self) -> None:
        """Test that category column is indexed."""
        category_column = PromptTemplate.__table__.c.category
        assert category_column.index is True

    def test_template_created_by_is_indexed(self) -> None:
        """Test that created_by column is indexed."""
        created_by_column = PromptTemplate.__table__.c.created_by
        assert created_by_column.index is True

    def test_template_description_is_nullable(self) -> None:
        """Test that description is nullable."""
        description_column = PromptTemplate.__table__.c.description
        assert description_column.nullable is True

    def test_template_created_by_is_nullable(self) -> None:
        """Test that created_by is nullable."""
        created_by_column = PromptTemplate.__table__.c.created_by
        assert created_by_column.nullable is True

    def test_sync_variables_method(self) -> None:
        """Test sync_variables method extracts variables."""
        template = PromptTemplate(
            name="Test",
            template="Hello {name}, you have {count} messages",
            category="test",
            variables=["stale"],
        )

        template.sync_variables()

        assert template.variables == ["name", "count"]

    def test_sync_variables_event_before_insert(self) -> None:
        """Test that variables are synced before insert."""
        template = PromptTemplate(
            name="Auto Sync",
            template="Hello {user}!",
            category="test",
            variables=["old"],
        )

        _sync_prompt_template_variables(None, None, template)

        assert template.variables == ["user"]

    def test_sync_variables_event_before_update(self) -> None:
        """Test that variables are synced before update."""
        template = PromptTemplate(
            name="Update Sync",
            template="Original {name}",
            category="test",
            variables=["outdated"],
        )

        # Update template
        template.template = "Updated {recipient} from {sender}"
        _sync_prompt_template_variables(None, None, template)

        assert template.variables == ["recipient", "sender"]

    def test_template_id_is_uuid_string(self) -> None:
        """Test that template ID is generated as UUID string."""
        template1 = PromptTemplate(
            name="Template 1",
            template="Content 1",
            category="test",
        )
        template2 = PromptTemplate(
            name="Template 2",
            template="Content 2",
            category="test",
        )

        # IDs should be different UUIDs
        assert template1.id != template2.id
        # ID should be a 36-character UUID string
        assert len(template1.id) == 36

    def test_template_tags_default_empty_list(self) -> None:
        """Test that tags default to empty list."""
        template = PromptTemplate(
            name="No Tags",
            template="No tags template",
            category="test",
        )

        assert template.tags == []

    def test_template_variables_default_empty_list(self) -> None:
        """Test that variables default to empty list."""
        template = PromptTemplate(
            name="No Variables",
            template="No variables here",
            category="test",
        )

        assert template.variables == []

    def test_template_different_types(self) -> None:
        """Test creating templates with different types."""
        for template_type in TemplateType:
            template = PromptTemplate(
                name=f"Type {template_type.value}",
                template="Test template",
                category="test",
                type=template_type,
            )
            assert template.type == template_type

    def test_template_is_public_flag(self) -> None:
        """Test public/private template states."""
        public_template = PromptTemplate(
            name="Public",
            template="Public template",
            category="test",
            is_public=True,
        )
        private_template = PromptTemplate(
            name="Private",
            template="Private template",
            category="test",
            is_public=False,
        )

        assert public_template.is_public is True
        assert private_template.is_public is False
