# /home/mohith/Catchup-Mohith/backend/tests/unit/test_rate_limit_service.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from backend.app.core.config import settings
from backend.app.core.exceptions import AuthRateLimitedException
from backend.app.services.auth_service import AuthService


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def auth_service_for_rate_limit(mock_session, mock_cache):
    return AuthService(session=mock_session, cache=mock_cache)


@pytest.mark.asyncio
async def test_rate_limit_blocks_sixth_attempt(auth_service_for_rate_limit, mock_cache):
    mock_cache.get.return_value = str(settings.auth_rate_limit_attempts)
    with pytest.raises(AuthRateLimitedException):
        await auth_service_for_rate_limit.login("any@example.com", "any", "192.168.1.1")


@pytest.mark.asyncio
async def test_rate_limit_does_not_block_fifth_attempt(
    auth_service_for_rate_limit, mock_cache
):
    mock_cache.get.return_value = str(settings.auth_rate_limit_attempts - 1)
    from backend.app.models.user import User, UserRole

    user = MagicMock(spec=User)
    user.id = __import__("uuid").uuid4()
    user.hashed_password = "stubbed-hash"
    user.is_active = True
    user.token_version = 0
    user.role = UserRole.ADMIN
    with (
        patch.object(
            auth_service_for_rate_limit.user_repo,
            "get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "backend.app.services.auth_service.verify_password",
            new=lambda plain, _hashed: plain == "pass",
        ),
        patch(
            "backend.app.services.auth_service.get_user_version",
            new=AsyncMock(return_value=0),
        ),
        patch(
            "backend.app.services.auth_service.set_user_version",
            new=AsyncMock(),
        ),
    ):
        result = await auth_service_for_rate_limit.login(
            "any@example.com", "pass", "192.168.1.1"
        )
        assert result.access_token


@pytest.mark.asyncio
async def test_rate_limit_returns_none_on_redis_failure(mock_cache):
    mock_cache.get.return_value = None
    result = await mock_cache.get("stockbridge:ratelimit:auth:1.2.3.4", db=1)
    assert result is None


@pytest.mark.asyncio
async def test_rate_limit_ttl_set_on_first_attempt_only(
    auth_service_for_rate_limit, mock_cache
):
    mock_cache.get.return_value = None
    mock_cache.increment.return_value = 1

    from backend.app.models.user import User

    user = MagicMock(spec=User)
    user.id = __import__("uuid").uuid4()
    user.hashed_password = "stubbed-hash"
    user.is_active = True
    user.token_version = 0

    with (
        patch.object(
            auth_service_for_rate_limit.user_repo,
            "get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "backend.app.services.auth_service.verify_password",
            new=lambda plain, _hashed: plain == "correct_password",
        ),
    ):
        try:
            await auth_service_for_rate_limit.login("x@x.com", "wrongpass", "10.0.0.1")
        except Exception:
            pass
        mock_cache.set.assert_called_once()
        call_kwargs = mock_cache.set.call_args
        assert call_kwargs[1]["ttl"] == settings.auth_rate_limit_window_seconds
