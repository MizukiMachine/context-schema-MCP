"""Unit tests for OptimizationTask model."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models.optimization_task import OptimizationStatus, OptimizationTask


class TestOptimizationStatus:
    """Tests for OptimizationStatus enum."""

    def test_status_enum_values(self) -> None:
        """Test OptimizationStatus enum values."""
        assert OptimizationStatus.PENDING.value == "pending"
        assert OptimizationStatus.IN_PROGRESS.value == "in_progress"
        assert OptimizationStatus.COMPLETED.value == "completed"
        assert OptimizationStatus.FAILED.value == "failed"

    def test_status_enum_count(self) -> None:
        """Test that all expected statuses exist."""
        statuses = list(OptimizationStatus)
        assert len(statuses) == 4


class TestOptimizationTaskModel:
    """Tests for OptimizationTask model."""

    def test_create_task_with_required_fields(self) -> None:
        """Test creating a task with only required fields."""
        task = OptimizationTask(
            window_id="window-123",
            optimization_type="layout",
            goals=["reduce-latency"],
            parameters={"iterations": 10},
        )

        assert task.window_id == "window-123"
        assert task.optimization_type == "layout"
        assert task.goals == ["reduce-latency"]
        assert task.parameters == {"iterations": 10}
        assert task.status == OptimizationStatus.PENDING

    def test_create_task_with_all_fields(self) -> None:
        """Test creating a task with all fields."""
        task = OptimizationTask(
            window_id="window-456",
            optimization_type="compression",
            goals=["minimize-tokens", "maintain-quality"],
            parameters={"threshold": 0.5, "strategy": "semantic"},
            status=OptimizationStatus.IN_PROGRESS,
            progress=0.3,
            result={"intermediate": True},
            error_message=None,
            started_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            completed_at=None,
        )

        assert task.window_id == "window-456"
        assert task.optimization_type == "compression"
        assert task.goals == ["minimize-tokens", "maintain-quality"]
        assert task.parameters == {"threshold": 0.5, "strategy": "semantic"}
        assert task.status == OptimizationStatus.IN_PROGRESS
        assert task.progress == 0.3
        assert task.result == {"intermediate": True}
        assert task.error_message is None
        assert task.started_at == datetime(2026, 1, 15, tzinfo=timezone.utc)
        assert task.completed_at is None

    def test_task_table_name(self) -> None:
        """Test that table name is correct."""
        assert OptimizationTask.__tablename__ == "optimization_tasks"

    def test_task_window_id_is_indexed(self) -> None:
        """Test that window_id column is indexed."""
        window_id_column = OptimizationTask.__table__.c.window_id
        assert window_id_column.index is True

    def test_task_optimization_type_is_indexed(self) -> None:
        """Test that optimization_type column is indexed."""
        optimization_type_column = OptimizationTask.__table__.c.optimization_type
        assert optimization_type_column.index is True

    def test_task_default_status(self) -> None:
        """Test default status is PENDING."""
        task = OptimizationTask(
            window_id="window-default",
            optimization_type="test",
            goals=[],
            parameters={},
        )
        assert OptimizationTask.__table__.c.status.default.arg == OptimizationStatus.PENDING

    def test_task_default_progress(self) -> None:
        """Test default progress is 0.0."""
        task = OptimizationTask(
            window_id="window-progress",
            optimization_type="test",
            goals=[],
            parameters={},
        )
        assert OptimizationTask.__table__.c.progress.default.arg == 0.0


class TestMarkInProgress:
    """Tests for mark_in_progress method."""

    def test_mark_in_progress_basic(self) -> None:
        """Test basic mark_in_progress."""
        task = OptimizationTask(
            window_id="window-1",
            optimization_type="layout",
            goals=["speed"],
            parameters={},
        )
        task.result = {"old": True}
        task.error_message = "previous error"

        task.mark_in_progress(progress=0.4)

        assert task.status == OptimizationStatus.IN_PROGRESS
        assert task.progress == 0.4
        assert task.result is None
        assert task.error_message is None
        assert task.started_at is not None
        assert task.completed_at is None

    def test_mark_in_progress_normalizes_progress(self) -> None:
        """Test that mark_in_progress normalizes progress."""
        task = OptimizationTask(
            window_id="window-2",
            optimization_type="test",
            goals=[],
            parameters={},
        )

        task.mark_in_progress(progress=1.5)  # Over 1.0
        assert task.progress == 1.0

        task.mark_in_progress(progress=-0.5)  # Under 0.0
        assert task.progress == 0.0

    def test_mark_in_progress_default_progress(self) -> None:
        """Test mark_in_progress with no progress argument."""
        task = OptimizationTask(
            window_id="window-3",
            optimization_type="test",
            goals=[],
            parameters={},
        )

        task.mark_in_progress()

        assert task.progress == 0.0

    def test_mark_in_progress_preserves_started_at(self) -> None:
        """Test that started_at is not overwritten if already set."""
        original_time = datetime(2025, 12, 25, tzinfo=timezone.utc)
        task = OptimizationTask(
            window_id="window-4",
            optimization_type="test",
            goals=[],
            parameters={},
        )
        task.started_at = original_time

        task.mark_in_progress()

        # started_at should remain the original time
        assert task.started_at == original_time


class TestMarkCompleted:
    """Tests for mark_completed method."""

    def test_mark_completed_basic(self) -> None:
        """Test basic mark_completed."""
        task = OptimizationTask(
            window_id="window-5",
            optimization_type="layout",
            goals=["maximize-throughput"],
            parameters={"temperature": 0.2},
        )

        task.mark_completed(result={"score": 0.95})

        assert task.status == OptimizationStatus.COMPLETED
        assert task.progress == 1.0
        assert task.result == {"score": 0.95}
        assert task.error_message is None
        assert task.started_at is not None
        assert task.completed_at is not None

    def test_mark_completed_no_result(self) -> None:
        """Test mark_completed without result."""
        task = OptimizationTask(
            window_id="window-6",
            optimization_type="test",
            goals=[],
            parameters={},
        )

        task.mark_completed()

        assert task.result is None
        assert task.status == OptimizationStatus.COMPLETED

    def test_mark_completed_sets_progress_to_one(self) -> None:
        """Test that mark_completed always sets progress to 1.0."""
        task = OptimizationTask(
            window_id="window-7",
            optimization_type="test",
            goals=[],
            parameters={},
        )
        task.progress = 0.5

        task.mark_completed()

        assert task.progress == 1.0


class TestMarkFailed:
    """Tests for mark_failed method."""

    def test_mark_failed_basic(self) -> None:
        """Test basic mark_failed."""
        task = OptimizationTask(
            window_id="window-8",
            optimization_type="layout",
            goals=["improve-quality"],
            parameters={"batch_size": 4},
        )
        task.result = {"partial": True}

        task.mark_failed("optimizer crashed")

        assert task.status == OptimizationStatus.FAILED
        assert task.result is None
        assert task.error_message == "optimizer crashed"
        assert task.started_at is not None
        assert task.completed_at is not None

    def test_mark_failed_clears_result(self) -> None:
        """Test that mark_failed clears result."""
        task = OptimizationTask(
            window_id="window-9",
            optimization_type="test",
            goals=[],
            parameters={},
        )
        task.result = {"should": "be cleared"}

        task.mark_failed("error")

        assert task.result is None


class TestProgressNormalization:
    """Tests for progress normalization."""

    def test_normalize_negative_value(self) -> None:
        """Test normalizing negative progress."""
        assert OptimizationTask._normalize_progress(-0.5) == 0.0

    def test_normalize_zero(self) -> None:
        """Test normalizing zero progress."""
        assert OptimizationTask._normalize_progress(0.0) == 0.0

    def test_normalize_valid_value(self) -> None:
        """Test normalizing valid progress."""
        assert OptimizationTask._normalize_progress(0.25) == 0.25
        assert OptimizationTask._normalize_progress(0.5) == 0.5
        assert OptimizationTask._normalize_progress(0.75) == 0.75

    def test_normalize_one(self) -> None:
        """Test normalizing 100% progress."""
        assert OptimizationTask._normalize_progress(1.0) == 1.0

    def test_normalize_over_one(self) -> None:
        """Test normalizing progress over 100%."""
        assert OptimizationTask._normalize_progress(1.5) == 1.0
        assert OptimizationTask._normalize_progress(2.0) == 1.0
        assert OptimizationTask._normalize_progress(100.0) == 1.0


class TestUpdateStatus:
    """Tests for update_status method."""

    def test_update_status_to_in_progress(self) -> None:
        """Test update_status to IN_PROGRESS."""
        task = OptimizationTask(
            window_id="window-10",
            optimization_type="layout",
            goals=["stabilize-output"],
            parameters={"seed": 42},
        )

        task.update_status(OptimizationStatus.IN_PROGRESS, progress=0.3)

        assert task.status == OptimizationStatus.IN_PROGRESS
        assert task.progress == 0.3
        assert task.started_at is not None
        assert task.completed_at is None

    def test_update_status_to_completed(self) -> None:
        """Test update_status to COMPLETED."""
        task = OptimizationTask(
            window_id="window-11",
            optimization_type="test",
            goals=[],
            parameters={},
        )

        task.update_status(OptimizationStatus.COMPLETED, result={"winner": "candidate-a"})

        assert task.status == OptimizationStatus.COMPLETED
        assert task.progress == 1.0
        assert task.result == {"winner": "candidate-a"}
        assert task.completed_at is not None

    def test_update_status_to_failed(self) -> None:
        """Test update_status to FAILED."""
        task = OptimizationTask(
            window_id="window-12",
            optimization_type="test",
            goals=[],
            parameters={},
        )

        task.update_status(OptimizationStatus.FAILED, error_message="Custom error")

        assert task.status == OptimizationStatus.FAILED
        assert task.error_message == "Custom error"
        assert task.completed_at is not None

    def test_update_status_to_failed_default_message(self) -> None:
        """Test update_status to FAILED with default message."""
        task = OptimizationTask(
            window_id="window-13",
            optimization_type="test",
            goals=[],
            parameters={},
        )

        task.update_status(OptimizationStatus.FAILED)

        assert task.error_message == "Optimization task failed."

    def test_update_status_to_pending_resets(self) -> None:
        """Test update_status to PENDING resets task state."""
        task = OptimizationTask(
            window_id="window-14",
            optimization_type="test",
            goals=[],
            parameters={},
        )
        # Set some state first
        task.status = OptimizationStatus.COMPLETED
        task.progress = 1.0
        task.result = {"old": "result"}
        task.error_message = "old error"
        task.started_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        task.completed_at = datetime(2025, 1, 2, tzinfo=timezone.utc)

        task.update_status(OptimizationStatus.PENDING, progress=2.0)

        assert task.status == OptimizationStatus.PENDING
        assert task.progress == 1.0  # Normalized from 2.0
        assert task.result is None
        assert task.error_message is None
        assert task.started_at is None
        assert task.completed_at is None

    def test_update_status_to_pending_default_progress(self) -> None:
        """Test update_status to PENDING with no progress uses 0."""
        task = OptimizationTask(
            window_id="window-15",
            optimization_type="test",
            goals=[],
            parameters={},
        )

        task.update_status(OptimizationStatus.PENDING)

        assert task.progress == 0.0


class TestOptimizationTaskId:
    """Tests for OptimizationTask ID generation."""

    def test_task_id_is_uuid_string(self) -> None:
        """Test that task ID is generated as UUID string."""
        task1 = OptimizationTask(
            window_id="window-a",
            optimization_type="type1",
            goals=[],
            parameters={},
        )
        task2 = OptimizationTask(
            window_id="window-b",
            optimization_type="type2",
            goals=[],
            parameters={},
        )

        # IDs should be different UUIDs
        assert task1.id != task2.id
        # ID should be a 36-character UUID string
        assert len(task1.id) == 36
        assert task1.id.count("-") == 4


class TestOptimizationTaskGoalsAndParameters:
    """Tests for goals and parameters fields."""

    def test_goals_default_empty_list(self) -> None:
        """Test that goals default to empty list."""
        assert OptimizationTask.__table__.c.goals.default.arg == []

    def test_parameters_default_empty_dict(self) -> None:
        """Test that parameters default to empty dict."""
        assert OptimizationTask.__table__.c.parameters.default.arg == {}

    def test_multiple_goals(self) -> None:
        """Test task with multiple goals."""
        task = OptimizationTask(
            window_id="window-multi",
            optimization_type="comprehensive",
            goals=["reduce-latency", "improve-quality", "minimize-cost"],
            parameters={},
        )

        assert len(task.goals) == 3
        assert "reduce-latency" in task.goals
        assert "improve-quality" in task.goals
        assert "minimize-cost" in task.goals

    def test_complex_parameters(self) -> None:
        """Test task with complex parameters."""
        task = OptimizationTask(
            window_id="window-complex",
            optimization_type="advanced",
            goals=[],
            parameters={
                "iterations": 100,
                "threshold": 0.95,
                "strategy": "semantic-compression",
                "options": {"parallel": True, "batch_size": 16},
            },
        )

        assert task.parameters["iterations"] == 100
        assert task.parameters["threshold"] == 0.95
        assert task.parameters["options"]["parallel"] is True
