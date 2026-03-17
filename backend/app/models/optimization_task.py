from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, Float, JSON, String, Text
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class OptimizationStatus(str, enum.Enum):
    """Status of an optimization task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationTask(Base, UUIDMixin, TimestampMixin):
    """Model for tracking optimization tasks."""

    __tablename__ = "optimization_tasks"

    window_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    optimization_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    goals: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    status: Mapped[OptimizationStatus] = mapped_column(
        Enum(OptimizationStatus, native_enum=False),
        nullable=False,
        default=OptimizationStatus.PENDING,
    )
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    result: Mapped[dict[str, Any] | None] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @staticmethod
    def _normalize_progress(progress: float) -> float:
        """Normalize progress to be between 0.0 and 1.0."""
        return max(0.0, min(1.0, progress))

    def mark_in_progress(self, progress: float = 0.0) -> None:
        """Mark the task as in progress."""
        self.status = OptimizationStatus.IN_PROGRESS
        self.progress = self._normalize_progress(progress)
        self.result = None
        self.error_message = None
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        self.completed_at = None

    def mark_completed(self, result: dict[str, Any] | None = None) -> None:
        """Mark the task as completed successfully."""
        self.status = OptimizationStatus.COMPLETED
        self.progress = 1.0
        self.result = result
        self.error_message = None
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error_message: str) -> None:
        """Mark the task as failed with an error message."""
        self.status = OptimizationStatus.FAILED
        self.result = None
        self.error_message = error_message
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        self.completed_at = datetime.now(timezone.utc)

    def update_status(
        self,
        status: OptimizationStatus,
        *,
        progress: float | None = None,
        result: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Update the task status with optional parameters.

        Args:
            status: New status to set
            progress: Progress value (only for IN_PROGRESS)
            result: Result data (only for COMPLETED)
            error_message: Error message (only for FAILED)
        """
        if status is OptimizationStatus.IN_PROGRESS:
            self.mark_in_progress(0.0 if progress is None else progress)
            return

        if status is OptimizationStatus.COMPLETED:
            self.mark_completed(result=result)
            return

        if status is OptimizationStatus.FAILED:
            self.mark_failed(error_message=error_message or "Optimization task failed.")
            return

        # PENDING - reset to initial state
        self.status = OptimizationStatus.PENDING
        self.progress = self._normalize_progress(0.0 if progress is None else progress)
        self.result = None
        self.error_message = None
        self.started_at = None
        self.completed_at = None
