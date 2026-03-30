# /home/mohith/Catchup-Mohith/backend/app/services/user_service.py
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    ConflictException,
    InvalidParameterException,
    NotFoundException,
    PageLimitExceededException,
)
from backend.app.core.security import hash_password
from backend.app.models.user import User, UserRole
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.common import ListResponse, make_pagination_meta
from backend.app.schemas.user import UserCreate, UserListParams, UserRead, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def list_users(self, params: UserListParams) -> ListResponse[UserRead]:
        if params.page_size > 50:
            raise PageLimitExceededException(
                details={"max": 50, "requested": params.page_size}
            )

        users, total = await self.repo.list_users(params)

        return ListResponse(
            data=[UserRead.model_validate(user) for user in users],
            meta=make_pagination_meta(
                total=total,
                page=params.page,
                page_size=params.page_size,
            ),
        )

    async def get_user(self, user_id: UUID) -> UserRead:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException(message=f"User with id={user_id} not found")
        return UserRead.model_validate(user)

    async def create_user(self, data: UserCreate) -> UserRead:
        if await self.repo.email_exists(data.email):
            raise ConflictException(
                details={
                    "field": "email",
                    "value": data.email,
                    "message": "A user with this email already exists",
                }
            )

        hashed = hash_password(data.password)
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hashed,
            role=data.role,
            is_active=data.is_active,
            token_version=0,
        )

        tx = (
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        async with tx:
            created = await self.repo.create(user)

        return UserRead.model_validate(created)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserRead:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException(message=f"User with id={user_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return UserRead.model_validate(user)

        tx = (
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        async with tx:
            updated = await self.repo.update(user_id, update_data)

        return UserRead.model_validate(updated)

    async def delete_user(self, user_id: UUID, actor_id: UUID) -> None:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException(message=f"User with id={user_id} not found")

        if user.id == actor_id:
            raise InvalidParameterException(
                message="You cannot delete your own account",
                details={"user_id": str(user_id)},
            )

        if user.role == UserRole.ADMIN:
            admin_count = await self.repo.count_admins()
            if admin_count <= 1:
                raise InvalidParameterException(
                    message="Cannot delete the last admin user",
                    details={"user_id": str(user_id)},
                )

        tx = (
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        async with tx:
            await self.repo.soft_delete(user_id)
