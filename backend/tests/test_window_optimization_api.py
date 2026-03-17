from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.main import create_app
from app.models.context_element import ContextElement, ContextElementRole
from app.models.user import User
from app.services.context_optimizer import OptimizationResult, OptimizationType, get_context_optimizer


async def _create_test_user(async_db_session: AsyncSession) -> User:
    user = User(
        email="optimizer-api@example.com",
        username="optimizer-api",
        hashed_password="not-used",
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


def _build_snapshot(
    *,
    role: ContextElementRole,
    content: str,
    token_count: int,
    metadata: dict | None = None,
) -> ContextElement:
    return ContextElement(
        window_id="window-1",
        role=role,
        content=content,
        token_count=token_count,
        metadata_=metadata or {},
    )


@pytest.mark.asyncio
async def test_window_optimize_endpoints_return_before_after_comparison(
    async_db_session: AsyncSession,
) -> None:
    user = await _create_test_user(async_db_session)
    app = create_app()
    optimizer_calls: list[tuple[str, dict]] = []

    async def override_db():
        yield async_db_session

    async def override_current_user() -> User:
        return user

    class FakeContextOptimizer:
        async def optimize(self, elements, optimization_type, params):
            optimizer_calls.append((str(optimization_type), params))
            return OptimizationResult(
                original_elements=[
                    _build_snapshot(
                        role=ContextElementRole.USER,
                        content="Original verbose request about optimizing the migration window.",
                        token_count=20,
                    )
                ],
                optimized_elements=[
                    _build_snapshot(
                        role=ContextElementRole.USER,
                        content="Optimized migration request summary.",
                        token_count=12,
                        metadata={"relevance_score": 0.91},
                    )
                ],
                strategy_used=OptimizationType.TOKEN_REDUCTION,
                token_savings=8,
                quality_improvement=6.5,
            )

        async def auto_optimize(self, elements, params):
            optimizer_calls.append(("auto", params))
            return OptimizationResult(
                original_elements=[
                    _build_snapshot(
                        role=ContextElementRole.USER,
                        content="Original verbose request about optimizing the migration window.",
                        token_count=20,
                    )
                ],
                optimized_elements=[
                    _build_snapshot(
                        role=ContextElementRole.USER,
                        content="Optimized migration request summary.",
                        token_count=12,
                    )
                ],
                strategy_used=OptimizationType.TOKEN_REDUCTION,
                token_savings=8,
                quality_improvement=6.5,
            )

    def override_context_optimizer() -> FakeContextOptimizer:
        return FakeContextOptimizer()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_context_optimizer] = override_context_optimizer

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        create_session_response = await client.post(
            "/sessions",
            json={"name": "Optimization Session", "description": "Test session"},
        )
        assert create_session_response.status_code == 201
        session_id = create_session_response.json()["id"]

        create_window_response = await client.post(
            "/windows",
            json={
                "session_id": session_id,
                "name": "Optimization Window",
                "provider": "openai",
                "model": "gpt-4.1",
                "system_prompt": "Be concise",
                "token_limit": 128,
            },
        )
        assert create_window_response.status_code == 201
        window_id = create_window_response.json()["id"]

        create_element_response = await client.post(
            "/elements",
            json={
                "window_id": window_id,
                "role": "user",
                "content": "Need a verbose optimization example for the endpoint test.",
                "token_count": 15,
                "metadata": {},
            },
        )
        assert create_element_response.status_code == 201

        optimize_response = await client.post(
            f"/api/v1/windows/{window_id}/optimize",
            json={
                "optimization_type": "token_reduction",
                "params": {"target_reduction_ratio": 0.2},
            },
        )
        assert optimize_response.status_code == 200
        optimize_body = optimize_response.json()
        assert optimize_body["strategy_used"] == "token_reduction"
        assert optimize_body["token_savings"] == 8
        assert optimize_body["token_reduction_ratio"] == 0.4
        assert optimize_body["original_elements"][0]["content"].startswith("Original verbose")
        assert optimize_body["optimized_elements"][0]["metadata"] == {"relevance_score": 0.91}

        auto_optimize_response = await client.post(
            f"/api/v1/windows/{window_id}/auto-optimize",
            json={"params": {}},
        )
        assert auto_optimize_response.status_code == 200
        auto_body = auto_optimize_response.json()
        assert auto_body["strategy_used"] == "token_reduction"
        assert auto_body["optimized_token_count"] == 12

    assert optimizer_calls == [
        ("OptimizationType.TOKEN_REDUCTION", {"target_reduction_ratio": 0.2, "token_limit": 128}),
        ("auto", {"token_limit": 128}),
    ]
