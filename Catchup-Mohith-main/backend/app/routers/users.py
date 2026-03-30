# /home/mohith/Catchup-Mohith/backend/app/routers/users.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import require_role
from backend.app.core.exceptions import PageLimitExceededException
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.common import ListResponse, SingleResponse
from backend.app.schemas.user import UserCreate, UserListParams, UserRead, UserUpdate
from backend.app.services.user_service import UserService

router = APIRouter()


@router.get(
    "/",
    response_model=ListResponse[UserRead],
    summary="List users with optional filters",
)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> ListResponse[UserRead]:
    if page_size > 50:
        raise PageLimitExceededException(details={"max": 50, "requested": page_size})

    params = UserListParams(
        page=page,
        page_size=page_size,
        role=role,
        is_active=is_active,
        search=search,
    )
    service = UserService(session)
    return await service.list_users(params)


@router.get(
    "/{id}",
    response_model=SingleResponse[UserRead],
    summary="Get user by ID",
)
async def get_user(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[UserRead]:
    service = UserService(session)
    user = await service.get_user(id)
    return SingleResponse(data=user)


@router.post(
    "/",
    response_model=SingleResponse[UserRead],
    status_code=201,
    summary="Create a new user",
)
async def create_user(
    body: UserCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[UserRead]:
    service = UserService(session)
    user = await service.create_user(body)
    return SingleResponse(data=user)


@router.patch(
    "/{id}",
    response_model=SingleResponse[UserRead],
    summary="Update user role, status, or name",
)
async def update_user(
    id: UUID,
    body: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[UserRead]:
    service = UserService(session)
    user = await service.update_user(id, body)
    return SingleResponse(data=user)


@router.delete(
    "/{id}",
    response_model=SingleResponse[dict],
    summary="Soft-delete user",
)
async def delete_user(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[dict]:
    service = UserService(session)
    await service.delete_user(user_id=id, actor_id=current_user.id)
    return SingleResponse(data={"message": "User deleted successfully"})
