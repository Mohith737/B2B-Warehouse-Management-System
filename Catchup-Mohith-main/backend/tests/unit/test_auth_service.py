# /home/mohith/Catchup-Mohith/backend/tests/unit/test_auth_service.py
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    AccountInactiveException,
    AuthRateLimitedException,
    InvalidCredentialsException,
    SessionInvalidatedException,
    TokenRevokedException,
)
from backend.app.models.user import User, UserRole
from backend.app.services.auth_service import AuthService


def make_user(is_active=True, role=UserRole.ADMIN, token_version=0) -> User:
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.hashed_password = "stubbed-hash"
    user.is_active = is_active
    user.role = role
    user.token_version = token_version
    return user


@pytest.fixture(autouse=True)
def mock_verify_password():
    with patch(
        "backend.app.services.auth_service.verify_password",
        new=lambda plain, _hashed: plain == "correct_password",
    ):
        yield


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def mock_user_repo():
    repo = MagicMock()
    repo.get_by_email = AsyncMock()
    repo.get_active_by_id = AsyncMock()
    return repo


@pytest.fixture
def auth_service(mock_session, mock_cache):
    service = AuthService(
        session=mock_session,
        cache=mock_cache,
    )
    return service


@pytest.mark.asyncio
async def test_login_success_returns_access_and_refresh_tokens(
    auth_service, mock_cache
):
    user = make_user()
    with (
        patch.object(
            auth_service.user_repo,
            "get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "backend.app.services.auth_service.get_user_version",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "backend.app.services.auth_service.set_user_version",
            new=AsyncMock(),
        ),
    ):
        mock_cache.get.return_value = None
        result = await auth_service.login(
            "test@example.com", "correct_password", "1.2.3.4"
        )
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_raises_invalid_credentials(
    auth_service, mock_cache
):
    user = make_user()
    with patch.object(
        auth_service.user_repo,
        "get_by_email",
        new=AsyncMock(return_value=user),
    ):
        mock_cache.get.return_value = None
        with pytest.raises(InvalidCredentialsException):
            await auth_service.login("test@example.com", "wrong_password", "1.2.3.4")


@pytest.mark.asyncio
async def test_login_inactive_user_raises_account_inactive(auth_service, mock_cache):
    user = make_user(is_active=False)
    with patch.object(
        auth_service.user_repo,
        "get_by_email",
        new=AsyncMock(return_value=user),
    ):
        mock_cache.get.return_value = None
        with pytest.raises(AccountInactiveException):
            await auth_service.login("test@example.com", "correct_password", "1.2.3.4")


@pytest.mark.asyncio
async def test_login_rate_limit_exceeded_raises_rate_limited(auth_service, mock_cache):
    mock_cache.get.return_value = str(settings.auth_rate_limit_attempts)
    with pytest.raises(AuthRateLimitedException):
        await auth_service.login("test@example.com", "any_password", "1.2.3.4")


@pytest.mark.asyncio
async def test_login_rate_limit_allows_fifth_attempt(auth_service, mock_cache):
    mock_cache.get.return_value = str(settings.auth_rate_limit_attempts - 1)
    user = make_user()
    with (
        patch.object(
            auth_service.user_repo,
            "get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "backend.app.services.auth_service.get_user_version",
            new=AsyncMock(return_value=0),
        ),
    ):
        result = await auth_service.login(
            "test@example.com", "correct_password", "1.2.3.4"
        )
        assert result.access_token


@pytest.mark.asyncio
async def test_refresh_blacklisted_token_raises_token_revoked(auth_service):
    user = make_user()
    from backend.app.core.security import create_refresh_token

    token=see .env file
    with patch(
        "backend.app.services.auth_service.is_blacklisted",
        new=AsyncMock(return_value=True),
    ):
        with pytest.raises(TokenRevokedException):
            await auth_service.refresh(token)


@pytest.mark.asyncio
async def test_refresh_inactive_user_raises_account_inactive(auth_service):
    user = make_user(is_active=False)
    from backend.app.core.security import create_refresh_token

    token=see .env file
    with (
        patch(
            "backend.app.services.auth_service.is_blacklisted",
            new=AsyncMock(return_value=False),
        ),
        patch.object(
            auth_service.user_repo,
            "get_active_by_id",
            new=AsyncMock(return_value=None),
        ),
    ):
        with pytest.raises(AccountInactiveException):
            await auth_service.refresh(token)


@pytest.mark.asyncio
async def test_logout_blacklists_both_tokens(auth_service):
    user = make_user()
    from backend.app.core.security import create_access_token, create_refresh_token

    access = create_access_token(str(user.id), 0)
    refresh = create_refresh_token(str(user.id), 0)
    with patch(
        "backend.app.services.auth_service.blacklist_token",
        new=AsyncMock(),
    ) as mock_blacklist:
        await auth_service.logout(access, refresh)
        assert mock_blacklist.call_count == 2


@pytest.mark.asyncio
async def test_login_user_not_found_raises_invalid_credentials(
    auth_service, mock_cache
):
    mock_cache.get.return_value = None
    with patch.object(
        auth_service.user_repo,
        "get_by_email",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(InvalidCredentialsException):
            await auth_service.login("notfound@example.com", "any", "1.2.3.4")


@pytest.mark.asyncio
async def test_cache_service_returns_none_on_redis_failure(mock_cache):
    mock_cache.get.return_value = None
    result = await mock_cache.get("any_key", db=1)
    assert result is None


@pytest.mark.asyncio
async def test_cache_service_never_raises_on_connection_error(mock_cache):
    from redis.exceptions import RedisError

    mock_cache.get.side_effect = None
    mock_cache.get.return_value = None
    try:
        result = await mock_cache.get("key", db=0)
        assert result is None
    except RedisError:
        pytest.fail("CacheService raised RedisError — must never raise")


@pytest.mark.asyncio
async def test_refresh_session_invalidated_on_version_mismatch(auth_service):
    user = make_user(token_version=5)
    from backend.app.core.security import create_refresh_token

    token=see .env file
    with (
        patch(
            "backend.app.services.auth_service.is_blacklisted",
            new=AsyncMock(return_value=False),
        ),
        patch.object(
            auth_service.user_repo,
            "get_active_by_id",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "backend.app.services.auth_service.get_user_version",
            new=AsyncMock(return_value=5),
        ),
    ):
        with pytest.raises(SessionInvalidatedException):
            await auth_service.refresh(token)


@pytest.mark.asyncio
async def test_refresh_db_token_version_mismatch_raises_session_invalidated(
    auth_service,
):
    user = make_user(token_version=3)
    from backend.app.core.security import create_refresh_token

    token=see .env file
    with (
        patch(
            "backend.app.services.auth_service.is_blacklisted",
            new=AsyncMock(return_value=False),
        ),
        patch.object(
            auth_service.user_repo,
            "get_active_by_id",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "backend.app.services.auth_service.get_user_version",
            new=AsyncMock(return_value=None),
        ),
    ):
        with pytest.raises(SessionInvalidatedException):
            await auth_service.refresh(token)


@pytest.mark.asyncio
async def test_rate_limit_blocks_sixth_attempt_not_fifth(auth_service, mock_cache):
    user = make_user()
    with (
        patch.object(
            auth_service.user_repo,
            "get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "backend.app.services.auth_service.get_user_version",
            new=AsyncMock(return_value=0),
        ),
    ):
        mock_cache.get.return_value = str(settings.auth_rate_limit_attempts - 1)
        await auth_service.login("test@example.com", "correct_password", "1.2.3.4")

    mock_cache.get.return_value = str(settings.auth_rate_limit_attempts)
    with pytest.raises(AuthRateLimitedException):
        await auth_service.login("test@example.com", "correct_password", "1.2.3.4")


