from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.routers.auth import router as auth_router


@pytest.mark.asyncio
async def test_auth_register_login_refresh_and_me(
    async_db_session: AsyncSession,
) -> None:
    app = FastAPI()
    app.include_router(auth_router)

    async def override_db_session():
        yield async_db_session

    app.dependency_overrides[get_db_session] = override_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        register_response = await client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "username": "tester",
                "password": "secret-password",
            },
        )

        assert register_response.status_code == 201
        register_body = register_response.json()
        assert register_body["token_type"] == "bearer"
        assert register_body["access_token"]
        assert register_body["refresh_token"]

        me_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {register_body['access_token']}"},
        )

        assert me_response.status_code == 200
        assert me_response.json()["email"] == "user@example.com"

        login_response = await client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "secret-password",
            },
        )

        assert login_response.status_code == 200
        login_body = login_response.json()
        assert login_body["access_token"]
        assert login_body["refresh_token"]

        refresh_response = await client.post(
            "/auth/refresh",
            json={"refresh_token": login_body["refresh_token"]},
        )

        assert refresh_response.status_code == 200
        refresh_body = refresh_response.json()
        assert refresh_body["access_token"]
        assert refresh_body["refresh_token"]


@pytest.mark.asyncio
async def test_auth_me_returns_401_for_invalid_token(
    async_db_session: AsyncSession,
) -> None:
    app = FastAPI()
    app.include_router(auth_router)

    async def override_db_session():
        yield async_db_session

    app.dependency_overrides[get_db_session] = override_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

    assert response.status_code == 401
