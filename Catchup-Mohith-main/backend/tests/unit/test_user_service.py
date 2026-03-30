# backend/tests/unit/test_user_service.py
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.app.core.exceptions import (
    ConflictException,
    InvalidParameterException,
    NotFoundException,
)
from backend.app.models.user import User, UserRole
from backend.app.schemas.user import UserCreate, UserListParams, UserUpdate
from backend.app.services.user_service import UserService


def make_user(
    *,
    role: UserRole = UserRole.PROCUREMENT_MANAGER,
    is_active: bool = True,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "user@example.com"
    user.full_name = "Test User"
    user.hashed_password = "hashed-password"
    user.role = role
    user.is_active = is_active
    user.token_version = 0
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    user.deleted_at = None
    return user


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.in_transaction = MagicMock(return_value=False)
    session.begin_nested = MagicMock(
        return_value=MagicMock(
            __aenter__=AsyncMock(return_value=None),
            __aexit__=AsyncMock(return_value=False),
        )
    )
    session.begin = MagicMock(
        return_value=MagicMock(
            __aenter__=AsyncMock(return_value=None),
            __aexit__=AsyncMock(return_value=False),
        )
    )
    return session


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.email_exists = AsyncMock(return_value=False)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.count_admins = AsyncMock(return_value=2)
    repo.list_users = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def service(mock_session, mock_repo):
    svc = UserService(mock_session)
    svc.repo = mock_repo
    return svc


@pytest.mark.asyncio
async def test_create_user_hashes_password(service, mock_repo, monkeypatch):
    created = make_user()
    mock_repo.create.return_value = created

    monkeypatch.setattr(
        "backend.app.services.user_service.hash_password",
        lambda plain: f"hashed::{plain}",
    )

    payload = UserCreate(
        email="new@example.com",
        full_name="New User",
        password=see .env file
        role=UserRole.WAREHOUSE_STAFF,
        is_active=True,
    )

    result = await service.create_user(payload)

    assert result.email == created.email
    created_arg = mock_repo.create.await_args.args[0]
    assert created_arg.hashed_password == "hashed::StrongPass123!"


@pytest.mark.asyncio
async def test_create_user_raises_conflict_on_duplicate_email(service, mock_repo):
    mock_repo.email_exists.return_value = True

    payload = UserCreate(
        email="dup@example.com",
        full_name="Duplicate",
        password=see .env file
        role=UserRole.ADMIN,
        is_active=True,
    )

    with pytest.raises(ConflictException):
        await service.create_user(payload)


@pytest.mark.asyncio
async def test_update_user_raises_not_found_for_missing_user(service, mock_repo):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_user(uuid4(), UserUpdate(full_name="Renamed"))


@pytest.mark.asyncio
async def test_delete_user_raises_invalid_param_when_deleting_self(service, mock_repo):
    user = make_user(role=UserRole.ADMIN)
    mock_repo.get_by_id.return_value = user

    with pytest.raises(InvalidParameterException):
        await service.delete_user(user_id=user.id, actor_id=user.id)


@pytest.mark.asyncio
async def test_delete_user_raises_invalid_param_when_last_admin(service, mock_repo):
    user = make_user(role=UserRole.ADMIN)
    mock_repo.get_by_id.return_value = user
    mock_repo.count_admins.return_value = 1

    with pytest.raises(InvalidParameterException):
        await service.delete_user(user_id=user.id, actor_id=uuid4())


@pytest.mark.asyncio
async def test_list_users_filters_by_role(service, mock_repo):
    manager = make_user(role=UserRole.PROCUREMENT_MANAGER)
    mock_repo.list_users.return_value = ([manager], 1)

    params = UserListParams(role=UserRole.PROCUREMENT_MANAGER)
    result = await service.list_users(params)

    assert result.meta.total == 1
    called_params = mock_repo.list_users.await_args.args[0]
    assert called_params.role == UserRole.PROCUREMENT_MANAGER


@pytest.mark.asyncio
async def test_list_users_filters_by_is_active(service, mock_repo):
    inactive = make_user(is_active=False)
    mock_repo.list_users.return_value = ([inactive], 1)

    params = UserListParams(is_active=False)
    result = await service.list_users(params)

    assert result.meta.total == 1
    called_params = mock_repo.list_users.await_args.args[0]
    assert called_params.is_active is False


