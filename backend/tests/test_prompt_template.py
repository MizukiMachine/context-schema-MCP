from __future__ import annotations

from app.models.prompt_template import (
    PromptTemplate,
    TemplateType,
    _sync_prompt_template_variables,
    extract_variables,
)


def test_extract_variables_basic() -> None:
    template = "Hello {name}, you have {count} messages from {sender}."

    assert extract_variables(template) == ["name", "count", "sender"]


def test_extract_variables_with_format() -> None:
    template = "Price: {price:.2f}, debug: {item!r}, padded: {code:>8}"

    assert extract_variables(template) == ["price", "item", "code"]


def test_extract_variables_nested() -> None:
    template = "User: {user.profile.name}, first item: {items[0].title}"

    assert extract_variables(template) == ["user", "items"]


def test_prompt_template_auto_sync() -> None:
    prompt_template = PromptTemplate(
        name="Greeting",
        description="Greeting template",
        template="Hello {name}",
        variables=["stale"],
        category="general",
        tags=["greeting"],
        created_by="user-1",
        is_public=True,
    )

    _sync_prompt_template_variables(None, None, prompt_template)

    assert prompt_template.variables == ["name"]

    prompt_template.template = "Hello {name} from {team}"
    prompt_template.variables = ["outdated"]
    _sync_prompt_template_variables(None, None, prompt_template)

    assert prompt_template.variables == ["name", "team"]


def test_prompt_template_create() -> None:
    prompt_template = PromptTemplate(
        name="Summarizer",
        description="Summarize content",
        template="Summarize {topic}",
        category="analysis",
        tags=["summary", "analysis"],
    )

    prompt_template.sync_variables()

    assert prompt_template.name == "Summarizer"
    assert prompt_template.description == "Summarize content"
    assert prompt_template.category == "analysis"
    assert prompt_template.tags == ["summary", "analysis"]
    assert prompt_template.variables == ["topic"]
    assert PromptTemplate.__table__.c.type.default.arg is TemplateType.COMPLETION
    assert PromptTemplate.__table__.c.usage_count.default.arg == 0
    assert PromptTemplate.__table__.c.quality_score.default.arg == 0.0
    assert PromptTemplate.__table__.c.is_public.default.arg is False
