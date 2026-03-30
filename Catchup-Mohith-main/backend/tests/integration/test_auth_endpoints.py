# /home/mohith/Catchup-Mohith/backend/tests/integration/test_auth_endpoints.py
import pytest
from backend.app.cache.service import cache_service
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_login_endpoint_returns_200_and_tokens(client, admin_user):
    response = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "see .env file",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client, admin_user):
    response = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "see .env file",
        },
    )
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_rate_limit_blocks_sixth_attempt(client, admin_user):
    ip = "10.10.10.10"
    rate_key = f"stockbridge:ratelimit:auth:{ip}"
    await cache_service.delete(rate_key, db=settings.redis_auth_db)

    headers = {"X-Forwarded-For": ip}
    for _ in range(settings.auth_rate_limit_attempts):
        await client.post(
            "/auth/login",
            json={
                "email": "admin@test.com",
                "password": "see .env file",
            },
            headers=headers,
        )
    response = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "see .env file",
        },
        headers=headers,
    )
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "AUTH_RATE_LIMITED"

    await cache_service.delete(rate_key, db=settings.redis_auth_db)


@pytest.mark.asyncio
async def test_logout_then_request_with_old_token_returns_401(
    client, admin_user, admin_token
):
    login_resp = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "see .env file",
        },
    )
    tokens=see .env file
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    logout_resp = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert logout_resp.status_code == 200

    response = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_REVOKED"


@pytest.mark.asyncio
async def test_logout_blacklists_refresh_token(client, admin_user):
    login_resp = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "see .env file",
        },
    )
    tokens=see .env file
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    await client.post(
        "/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_REVOKED"


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(client, admin_user):
    login_resp = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "see .env file",
        },
    )
    refresh = login_resp.json()["data"]["refresh_token"]
    original_access = login_resp.json()["data"]["access_token"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert response.status_code == 200
    new_access = response.json()["data"]["access_token"]
    assert new_access != original_access


@pytest.mark.asyncio
async def test_refresh_with_blacklisted_token_returns_401(client, admin_user):
    login_resp = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "see .env file",
        },
    )
    tokens=see .env file
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    await client.post(
        "/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_REVOKED"


@pytest.mark.asyncio
async def test_refresh_with_inactive_user_returns_401(client, inactive_user):
    from backend.app.core.security import create_refresh_token

    token=see .env file
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": token},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "ACCOUNT_INACTIVE"


@pytest.mark.asyncio
async def test_user_version_mismatch_returns_401_session_invalidated(
    client, admin_user
):
    login_resp = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "see .env file",
        },
    )
    access = login_resp.json()["data"]["access_token"]

    version_key = f"stockbridge:user_version:{admin_user.id}"
    await cache_service.increment(version_key, db=settings.redis_auth_db)

    response = await client.post(
        "/auth/logout",
        json={"refresh_token": "any"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_INVALIDATED"

    await cache_service.delete(version_key, db=settings.redis_auth_db)


