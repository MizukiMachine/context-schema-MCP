from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ContextWindow(Base, UUIDMixin, TimestampMixin):
    """Window configuration within a context session."""

    __tablename__ = "context_windows"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("context_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_limit: Mapped[int] = mapped_column(Integer, nullable=False)

    session: Mapped["ContextSession"] = relationship(back_populates="windows")
    elements: Mapped[list["ContextElement"]] = relationship(
        back_populates="window",
        cascade="all, delete-orphan",
    )
