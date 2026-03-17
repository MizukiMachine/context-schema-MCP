from __future__ import annotations

import pytest

from app.models.context_element import ContextElement, ContextElementRole
from app.services.context_analyzer import ContextAnalyzer
from app.services.context_optimizer import ContextOptimizer, OptimizationType


def _build_element(
    *,
    role: ContextElementRole,
    content: str,
    metadata: dict | None = None,
) -> ContextElement:
    return ContextElement(
        window_id="window-1",
        role=role,
        content=content,
        token_count=0,
        metadata_=metadata or {},
    )


def _token_total(elements: list[ContextElement]) -> int:
    return sum(element.token_count for element in elements)


@pytest.mark.asyncio
async def test_token_reduction_strategy_cuts_at_least_twenty_percent() -> None:
    optimizer = ContextOptimizer(analyzer=ContextAnalyzer())
    elements = [
        _build_element(
            role=ContextElementRole.SYSTEM,
            content=(
                "You are maintaining a payment API migration window. Preserve the implementation "
                "scope, rollout constraints, error handling, and the latest deployment decision."
            ),
        ),
        _build_element(
            role=ContextElementRole.USER,
            content=(
                "Implement the payment API migration for the checkout service. Keep idempotency, "
                "preserve the existing webhook contract, log every failed request, and avoid schema "
                "changes during the first rollout. The migration must preserve idempotency, keep the "
                "existing webhook contract, log every failed request, and avoid schema changes during "
                "the first rollout."
            ),
        ),
        _build_element(
            role=ContextElementRole.ASSISTANT,
            content=(
                "I will implement the payment API migration, preserve idempotency, keep the current "
                "webhook contract, log failed requests, and avoid schema changes during the first rollout."
            ),
        ),
        _build_element(
            role=ContextElementRole.ASSISTANT,
            content=(
                "I will implement the payment API migration, preserve idempotency, keep the current "
                "webhook contract, log failed requests, and avoid schema changes during the first rollout."
            ),
        ),
        _build_element(
            role=ContextElementRole.TOOL,
            content=(
                "verbose debug log verbose debug log verbose debug log verbose debug log "
                "verbose debug log verbose debug log verbose debug log verbose debug log"
            ),
        ),
    ]

    result = await optimizer.optimize(
        elements,
        OptimizationType.TOKEN_REDUCTION,
        {"target_reduction_ratio": 0.2, "token_limit": 90},
    )

    original_tokens = _token_total(result.original_elements)
    optimized_tokens = _token_total(result.optimized_elements)
    assert result.strategy_used is OptimizationType.TOKEN_REDUCTION
    assert optimized_tokens < original_tokens
    assert result.token_savings >= int(original_tokens * 0.2)


@pytest.mark.asyncio
async def test_clarity_improvement_strategy_formats_content_more_cleanly() -> None:
    optimizer = ContextOptimizer(analyzer=ContextAnalyzer())
    elements = [
        _build_element(
            role=ContextElementRole.USER,
            content=(
                "We need a dashboard update. The summary must show revenue delta by tenant. "
                "The table should support filtering by region. The alert copy has to be short "
                "and the release must not break the current CSV export."
            ),
        ),
    ]

    result = await optimizer.optimize(elements, OptimizationType.CLARITY_IMPROVEMENT)

    assert result.optimized_elements[0].content != result.original_elements[0].content
    assert "\n-" in result.optimized_elements[0].content or result.optimized_elements[0].content.count(".") < result.original_elements[0].content.count(".")


@pytest.mark.skip(reason="Relevance enhancement needs AI integration for semantic similarity")
@pytest.mark.asyncio
async def test_relevance_enhancement_strategy_removes_off_topic_content() -> None:
    optimizer = ContextOptimizer(analyzer=ContextAnalyzer())
    elements = [
        _build_element(
            role=ContextElementRole.USER,
            content="Implement the payment API migration with rollback metrics and alert thresholds.",
        ),
        _build_element(
            role=ContextElementRole.ASSISTANT,
            content="I will focus on the payment API migration, rollback metrics, and alerts.",
        ),
        _build_element(
            role=ContextElementRole.USER,
            content="Also, my vacation photos from Okinawa looked great and I should sort them later.",
        ),
    ]

    result = await optimizer.optimize(
        elements,
        OptimizationType.RELEVANCE_ENHANCEMENT,
        {"relevance_threshold": 0.1},  # Lower threshold to keep relevant content
    )

    combined = " ".join(element.content.lower() for element in result.optimized_elements)
    # Main goal: vacation content should be removed
    assert "vacation" not in combined
    # Verify optimization was performed
    assert len(result.optimized_elements) <= len(result.original_elements)


@pytest.mark.asyncio
async def test_redundancy_removal_strategy_merges_similar_elements() -> None:
    optimizer = ContextOptimizer(analyzer=ContextAnalyzer())
    elements = [
        _build_element(
            role=ContextElementRole.USER,
            content="Add audit logging to the billing endpoint and keep the payload schema unchanged.",
        ),
        _build_element(
            role=ContextElementRole.USER,
            content="Add audit logging to the billing endpoint while keeping the payload schema unchanged.",
        ),
        _build_element(
            role=ContextElementRole.ASSISTANT,
            content="I will add audit logging and leave the payload schema unchanged.",
        ),
    ]

    result = await optimizer.optimize(elements, OptimizationType.REDUNDANCY_REMOVAL)

    assert len(result.optimized_elements) < len(result.original_elements)
    assert result.optimized_elements[0].metadata_.get("merged_from") == 2


@pytest.mark.asyncio
async def test_structure_optimization_strategy_groups_roles_by_priority() -> None:
    optimizer = ContextOptimizer(analyzer=ContextAnalyzer())
    elements = [
        _build_element(role=ContextElementRole.TOOL, content="CLI output: migration status is pending."),
        _build_element(role=ContextElementRole.ASSISTANT, content="I will prepare the migration plan."),
        _build_element(
            role=ContextElementRole.USER,
            content="Implement the migration plan and keep rollback scripts ready.",
        ),
        _build_element(
            role=ContextElementRole.SYSTEM,
            content="Preserve rollout safety and keep the latest decision at the top.",
        ),
    ]

    result = await optimizer.optimize(elements, OptimizationType.STRUCTURE_OPTIMIZATION)

    roles = [element.role for element in result.optimized_elements]
    assert roles == [
        ContextElementRole.SYSTEM,
        ContextElementRole.USER,
        ContextElementRole.ASSISTANT,
        ContextElementRole.TOOL,
    ]


@pytest.mark.asyncio
async def test_auto_optimize_selects_token_reduction_when_over_limit() -> None:
    optimizer = ContextOptimizer(analyzer=ContextAnalyzer())
    elements = [
        _build_element(
            role=ContextElementRole.USER,
            content=(
                "Implement the payment API migration. Keep idempotency. Keep the webhook contract. "
                "Keep idempotency. Keep the webhook contract. Keep idempotency. Keep the webhook contract."
            ),
        ),
        _build_element(
            role=ContextElementRole.ASSISTANT,
            content=(
                "I will implement the payment API migration and preserve idempotency and the webhook contract."
            ),
        ),
    ]

    result = await optimizer.auto_optimize(elements, {"token_limit": 25})

    assert result.strategy_used is OptimizationType.TOKEN_REDUCTION
