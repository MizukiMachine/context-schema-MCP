from __future__ import annotations

import enum

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ContextSessionStatus(str, enum.Enum):
    """Available states for a context session."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class ContextSession(Base, UUIDMixin, TimestampMixin):
    """Top-level grouping for context windows."""

    __tablename__ = "context_sessions"

    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ContextSessionStatus] = mapped_column(
        Enum(ContextSessionStatus, native_enum=False),
        nullable=False,
        default=ContextSessionStatus.ACTIVE,
    )

    windows: Mapped[list["ContextWindow"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
