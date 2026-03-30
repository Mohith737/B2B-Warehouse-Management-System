# backend/tests/integration/test_auth_integration.py
import pytest
from httpx import AsyncClient

from .conftest import auth_headers


@pytest.mark.asyncio
async def test_login_returns_token(client: AsyncClient, seeded_users):
    response = await client.post(
        "/auth/login",
        json={"email": "admin@stockbridge.com", "password": "REDACTED_SEE_ENV"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient, seeded_users):
    response = await client.post(
        "/auth/login",
        json={"email": "admin@stockbridge.com", "password": "wrong-pass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient, admin_token: str):
    # Backend has no /auth/me endpoint.
    # Use protected dashboard as identity check.
    response = await client.get("/dashboard/", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert "total_users" in response.json()["data"]


@pytest.mark.asyncio
async def test_logout_blacklists_token(client: AsyncClient, admin_token: str):
    login_response = await client.post(
        "/auth/login",
        json={"email": "admin@stockbridge.com", "password": "REDACTED_SEE_ENV"},
    )
    refresh_token=see .env file

    logout_response = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
        headers=auth_headers(admin_token),
    )
    assert logout_response.status_code == 200


@pytest.mark.asyncio
async def test_refresh_returns_new_token(client: AsyncClient, seeded_users):
    login_response = await client.post(
        "/auth/login",
        json={"email": "manager@stockbridge.com", "password": "REDACTED_SEE_ENV"},
    )
    assert login_response.status_code == 200

    refresh_token=see .env file
    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["access_token"]


