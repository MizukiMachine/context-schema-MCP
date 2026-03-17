from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.main import create_app
from app.models.user import User
from app.services.context_analyzer import AnalysisResult, get_context_analyzer


async def _create_test_user(async_db_session: AsyncSession) -> User:
    user = User(
        email="api-user@example.com",
        username="api-user",
        hashed_password="not-used",
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_health_docs_and_crud_endpoints(async_db_session: AsyncSession) -> None:
    user = await _create_test_user(async_db_session)
    app = create_app()
    captured_window_ids: list[str] = []

    async def override_db():
        yield async_db_session

    async def override_current_user() -> User:
        return user

    class FakeContextAnalyzer:
        async def analyze(self, elements) -> AnalysisResult:
            captured_window_ids.extend([element.window_id for element in elements])
            return AnalysisResult(
                quality_score=82.5,
                topic_consistency=0.88,
                logical_flow=0.79,
                information_redundancy=0.18,
                token_efficiency=0.81,
                issues=["Context summary is missing."],
                recommendations=["Add a short summary at the top of the window."],
            )

    def override_context_analyzer() -> FakeContextAnalyzer:
        return FakeContextAnalyzer()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_context_analyzer] = override_context_analyzer

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        health_response = await client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json() == {"status": "ok", "version": "1.0.0"}

        docs_response = await client.get("/docs")
        assert docs_response.status_code == 200
        assert "Swagger UI" in docs_response.text

        invalid_session_response = await client.post("/sessions", json={"description": "missing name"})
        assert invalid_session_response.status_code == 422

        create_session_response = await client.post(
            "/sessions",
            json={"name": "Primary Session", "description": "Test session"},
        )
        assert create_session_response.status_code == 201
        session_body = create_session_response.json()
        assert session_body["name"] == "Primary Session"
        session_id = session_body["id"]

        list_sessions_response = await client.get("/sessions")
        assert list_sessions_response.status_code == 200
        assert len(list_sessions_response.json()) == 1

        create_window_response = await client.post(
            "/windows",
            json={
                "session_id": session_id,
                "name": "Main Window",
                "provider": "openai",
                "model": "gpt-4.1",
                "system_prompt": "Be precise",
                "token_limit": 4096,
            },
        )
        assert create_window_response.status_code == 201
        window_body = create_window_response.json()
        assert window_body["provider"] == "openai"
        window_id = window_body["id"]

        create_element_response = await client.post(
            "/elements",
            json={
                "window_id": window_id,
                "role": "user",
                "content": "hello",
                "token_count": 2,
                "metadata": {"source": "test"},
            },
        )
        assert create_element_response.status_code == 201
        element_body = create_element_response.json()
        assert element_body["metadata"] == {"source": "test"}
        element_id = element_body["id"]

        list_windows_response = await client.get("/windows", params={"session_id": session_id})
        assert list_windows_response.status_code == 200
        assert len(list_windows_response.json()) == 1

        list_elements_response = await client.get("/elements", params={"window_id": window_id})
        assert list_elements_response.status_code == 200
        assert len(list_elements_response.json()) == 1

        analyze_window_response = await client.post(f"/api/v1/windows/{window_id}/analyze")
        assert analyze_window_response.status_code == 200
        assert analyze_window_response.json()["quality_score"] == 82.5
        assert analyze_window_response.json()["issues"] == ["Context summary is missing."]
        assert captured_window_ids == [window_id]

        update_session_response = await client.patch(
            f"/sessions/{session_id}",
            json={"status": "archived"},
        )
        assert update_session_response.status_code == 200
        assert update_session_response.json()["status"] == "archived"

        update_window_response = await client.patch(
            f"/windows/{window_id}",
            json={"token_limit": 8192},
        )
        assert update_window_response.status_code == 200
        assert update_window_response.json()["token_limit"] == 8192

        update_element_response = await client.patch(
            f"/elements/{element_id}",
            json={"metadata": {"source": "updated"}, "content": "hello again"},
        )
        assert update_element_response.status_code == 200
        assert update_element_response.json()["metadata"] == {"source": "updated"}
        assert update_element_response.json()["content"] == "hello again"

        not_found_window_response = await client.get("/windows/missing-id")
        assert not_found_window_response.status_code == 404

        delete_element_response = await client.delete(f"/elements/{element_id}")
        assert delete_element_response.status_code == 204

        delete_window_response = await client.delete(f"/windows/{window_id}")
        assert delete_window_response.status_code == 204

        delete_session_response = await client.delete(f"/sessions/{session_id}")
        assert delete_session_response.status_code == 204
