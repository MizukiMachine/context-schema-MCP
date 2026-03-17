from __future__ import annotations

import pytest

from app.api.v1.windows import analyze_window
from app.models.context_element import ContextElement, ContextElementRole
from app.models.context_window import ContextWindow
from app.models.user import User
from app.services.context_analyzer import AnalysisResult


class FakeScalarResult:
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def all(self) -> list[object]:
        return self._values


class FakeExecuteResult:
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def scalars(self) -> FakeScalarResult:
        return FakeScalarResult(self._values)


class FakeAsyncSession:
    def __init__(self, elements: list[ContextElement]) -> None:
        self._elements = elements

    async def execute(self, _statement) -> FakeExecuteResult:
        return FakeExecuteResult(self._elements)


class FakeContextAnalyzer:
    def __init__(self) -> None:
        self.received_elements: list[ContextElement] = []

    async def analyze(self, elements: list[ContextElement]) -> AnalysisResult:
        self.received_elements = elements
        return AnalysisResult(
            quality_score=82.5,
            topic_consistency=0.88,
            logical_flow=0.79,
            information_redundancy=0.18,
            token_efficiency=0.81,
            issues=["Context summary is missing."],
            recommendations=["Add a short summary at the top of the window."],
        )


@pytest.mark.asyncio
async def test_analyze_window_endpoint(monkeypatch) -> None:
    user = User(
        id="user-1",
        email="api-user@example.com",
        username="api-user",
        hashed_password="not-used",
    )
    window = ContextWindow(
        id="window-1",
        session_id="session-1",
        name="Main Window",
        provider="openai",
        model="gpt-4.1",
        system_prompt="Be precise",
        token_limit=4096,
    )
    elements = [
        ContextElement(
            id="element-1",
            window_id="window-1",
            role=ContextElementRole.USER,
            content="Analyze this context window.",
            token_count=5,
            metadata_={},
        )
    ]
    analyzer = FakeContextAnalyzer()

    async def fake_get_owned_window(_db, window_id: str, user_id: str) -> ContextWindow | None:
        assert window_id == "window-1"
        assert user_id == "user-1"
        return window

    monkeypatch.setattr("app.api.v1.windows._get_owned_window", fake_get_owned_window)
    response = await analyze_window(
        window_id="window-1",
        db=FakeAsyncSession(elements),
        current_user=user,
        analyzer=analyzer,
    )

    assert response == AnalysisResult(
        quality_score=82.5,
        topic_consistency=0.88,
        logical_flow=0.79,
        information_redundancy=0.18,
        token_efficiency=0.81,
        issues=["Context summary is missing."],
        recommendations=["Add a short summary at the top of the window."],
    )
    assert analyzer.received_elements == elements
