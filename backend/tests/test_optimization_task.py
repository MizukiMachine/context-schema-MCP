from __future__ import annotations

from app.models.optimization_task import OptimizationStatus, OptimizationTask


def test_mark_in_progress() -> None:
    task = OptimizationTask(
        window_id="window-1",
        optimization_type="layout",
        goals=["reduce-latency"],
        parameters={"iterations": 10},
    )
    task.result = {"old": True}
    task.error_message = "previous error"

    task.mark_in_progress(progress=0.4)

    assert task.status is OptimizationStatus.IN_PROGRESS
    assert task.progress == 0.4
    assert task.result is None
    assert task.error_message is None
    assert task.started_at is not None
    assert task.completed_at is None


def test_mark_completed() -> None:
    task = OptimizationTask(
        window_id="window-1",
        optimization_type="layout",
        goals=["maximize-throughput"],
        parameters={"temperature": 0.2},
    )

    task.mark_completed(result={"score": 0.95})

    assert task.status is OptimizationStatus.COMPLETED
    assert task.progress == 1.0
    assert task.result == {"score": 0.95}
    assert task.error_message is None
    assert task.started_at is not None
    assert task.completed_at is not None


def test_mark_failed() -> None:
    task = OptimizationTask(
        window_id="window-1",
        optimization_type="layout",
        goals=["improve-quality"],
        parameters={"batch_size": 4},
    )
    task.result = {"partial": True}

    task.mark_failed("optimizer crashed")

    assert task.status is OptimizationStatus.FAILED
    assert task.result is None
    assert task.error_message == "optimizer crashed"
    assert task.started_at is not None
    assert task.completed_at is not None


def test_progress_normalization() -> None:
    assert OptimizationTask._normalize_progress(-0.5) == 0.0
    assert OptimizationTask._normalize_progress(0.25) == 0.25
    assert OptimizationTask._normalize_progress(1.5) == 1.0


def test_update_status() -> None:
    task = OptimizationTask(
        window_id="window-1",
        optimization_type="layout",
        goals=["stabilize-output"],
        parameters={"seed": 42},
    )

    task.update_status(OptimizationStatus.IN_PROGRESS, progress=0.3)
    assert task.status is OptimizationStatus.IN_PROGRESS
    assert task.progress == 0.3
    assert task.started_at is not None
    assert task.completed_at is None

    task.update_status(OptimizationStatus.COMPLETED, result={"winner": "candidate-a"})
    assert task.status is OptimizationStatus.COMPLETED
    assert task.progress == 1.0
    assert task.result == {"winner": "candidate-a"}
    assert task.completed_at is not None

    task.update_status(OptimizationStatus.PENDING, progress=2.0)
    assert task.status is OptimizationStatus.PENDING
    assert task.progress == 1.0
    assert task.result is None
    assert task.error_message is None
    assert task.started_at is None
    assert task.completed_at is None

    task.update_status(OptimizationStatus.FAILED)
    assert task.status is OptimizationStatus.FAILED
    assert task.error_message == "Optimization task failed."
    assert task.started_at is not None
    assert task.completed_at is not None
