from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import Enum, ForeignKey, Integer, JSON, Text
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ContextElementRole(str, enum.Enum):
    """Supported message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ContextElement(Base, UUIDMixin, TimestampMixin):
    """Atomic context element contained in a window."""

    __tablename__ = "context_elements"

    window_id: Mapped[str] = mapped_column(
        ForeignKey("context_windows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ContextElementRole] = mapped_column(
        Enum(ContextElementRole, native_enum=False),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )

    window: Mapped["ContextWindow"] = relationship(back_populates="elements")
