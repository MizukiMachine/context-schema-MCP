from __future__ import annotations

import enum
from string import Formatter

from sqlalchemy import Boolean, Enum, Float, Integer, JSON, String, Text, event
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class TemplateType(str, enum.Enum):
    """Types of prompt templates."""

    COMPLETION = "completion"
    CHAT = "chat"
    INSTRUCT = "instruct"
    FEWSHOT = "fewshot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    ROLEPLAY = "roleplay"


def extract_variables(template: str) -> list[str]:
    """
    Extract variable names from a template string.

    Handles format specifiers and attribute access:
    - {name} -> ["name"]
    - {name!r} -> ["name"]
    - {name:format} -> ["name"]
    - {user.name} -> ["user"]
    - {items[0]} -> ["items"]

    Args:
        template: Template string with {variable} placeholders

    Returns:
        List of unique variable names
    """
    variables: list[str] = []

    for _, field_name, _, _ in Formatter().parse(template):
        if not field_name:
            continue

        # Strip format specifiers and conversion flags
        normalized_name = field_name.split("!", 1)[0].split(":", 1)[0].strip()
        if not normalized_name:
            continue

        # Extract root variable name (before . or [)
        root_name = normalized_name.split(".", 1)[0].split("[", 1)[0]
        if root_name and root_name not in variables:
            variables.append(root_name)

    return variables


class PromptTemplate(Base, UUIDMixin, TimestampMixin):
    """Model for storing prompt templates with automatic variable extraction."""

    __tablename__ = "prompt_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    type: Mapped[TemplateType] = mapped_column(
        Enum(TemplateType, native_enum=False),
        nullable=False,
        default=TemplateType.COMPLETION,
    )
    category: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tags: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def sync_variables(self) -> None:
        """Extract and update variables from the template."""
        self.variables = extract_variables(self.template)


@event.listens_for(PromptTemplate, "before_insert")
@event.listens_for(PromptTemplate, "before_update")
def _sync_prompt_template_variables(
    _mapper: object, _connection: object, target: PromptTemplate
) -> None:
    """Automatically sync variables before insert and update."""
    target.sync_variables()
