from __future__ import annotations

import pytest

from app.models.context_element import ContextElement, ContextElementRole
from app.services.context_analyzer import ContextAnalyzer


class FakeGeminiService:
    def __init__(self, response: dict[str, list[str]]) -> None:
        self.response = response
        self.prompts: list[str] = []

    def generate_json(self, prompt: str) -> dict[str, list[str]]:
        self.prompts.append(prompt)
        return self.response


def _build_element(
    *,
    role: ContextElementRole,
    content: str,
    token_count: int,
) -> ContextElement:
    return ContextElement(
        window_id="window-1",
        role=role,
        content=content,
        token_count=token_count,
        metadata_={},
    )


@pytest.mark.asyncio
async def test_analyze_calculates_quality_and_merges_feedback() -> None:
    gemini = FakeGeminiService(
        {
            "issues": ["Important requirement is not summarized at the top."],
            "recommendations": ["Promote the final user goal into a short leading summary."],
        }
    )
    analyzer = ContextAnalyzer(gemini_service=gemini)
    elements = [
        _build_element(
            role=ContextElementRole.USER,
            content="Build the context analyzer service and add an API endpoint for analysis.",
            token_count=14,
        ),
        _build_element(
            role=ContextElementRole.ASSISTANT,
            content="I will implement the analyzer service, scoring logic, and endpoint wiring.",
            token_count=13,
        ),
        _build_element(
            role=ContextElementRole.USER,
            content="Build the context analyzer service and add an API endpoint for analysis.",
            token_count=14,
        ),
    ]

    result = await analyzer.analyze(elements)

    expected_quality = round(
        (
            result.topic_consistency * 0.35
            + result.logical_flow * 0.25
            + (1 - result.information_redundancy) * 0.2
            + result.token_efficiency * 0.2
        )
        * 100,
        2,
    )
    assert abs(result.quality_score - expected_quality) < 0.5  # Allow floating point tolerance
    assert result.information_redundancy > 0.3
    assert "Important requirement is not summarized at the top." in result.issues
    assert "Promote the final user goal into a short leading summary." in result.recommendations
    assert gemini.prompts


@pytest.mark.asyncio
async def test_analyze_handles_empty_context_without_gemini() -> None:
    analyzer = ContextAnalyzer()

    result = await analyzer.analyze([])

    assert result.quality_score == 0.0
    assert result.topic_consistency == 0.0
    assert result.issues == ["No context elements were provided for analysis."]
    assert result.recommendations == [
        "Add the key user requirements, constraints, and recent decisions to the window."
    ]
