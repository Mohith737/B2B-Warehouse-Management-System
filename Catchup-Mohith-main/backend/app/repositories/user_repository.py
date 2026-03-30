# /home/mohith/Catchup-Mohith/backend/app/repositories/user_repository.py
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import NotFoundException
from backend.app.models.user import User, UserRole
from backend.app.repositories.base_repository import BaseRepository
from backend.app.schemas.user import UserListParams


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id).where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email).where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_active_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User)
            .where(User.email == email)
            .where(User.is_active.is_(True))
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_active_by_id(self, id: UUID) -> User | None:
        result = await self.session.execute(
            select(User)
            .where(User.id == id)
            .where(User.is_active.is_(True))
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_users(self, params: UserListParams) -> tuple[list[User], int]:
        base_query = select(User).where(User.deleted_at.is_(None))

        if params.role is not None:
            base_query = base_query.where(User.role == params.role)

        if params.is_active is not None:
            base_query = base_query.where(and_(User.is_active.is_(params.is_active)))

        if params.search:
            search_term = f"%{params.search}%"
            base_query = base_query.where(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        skip = (params.page - 1) * params.page_size
        data_query = (
            base_query.order_by(User.created_at.desc())
            .offset(skip)
            .limit(params.page_size)
        )
        result = await self.session.execute(data_query)
        items = list(result.scalars().all())
        return items, total

    async def create(self, user_data: User) -> User:
        self.session.add(user_data)
        await self.session.flush()
        await self.session.refresh(user_data)
        return user_data

    async def update(self, user_id: UUID, update_data: dict[str, Any]) -> User:
        user = await self.get_by_id(user_id)
        if user is None:
            raise NotFoundException(
                message=f"User with id={user_id} not found",
                details={"resource": "User", "identifier": str(user_id)},
            )
        for key, value in update_data.items():
            setattr(user, key, value)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def soft_delete(self, user_id: UUID) -> User:
        user = await self.get_by_id(user_id)
        if user is None:
            raise NotFoundException(
                message=f"User with id={user_id} not found",
                details={"resource": "User", "identifier": str(user_id)},
            )
        user.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def increment_token_version(self, user: User) -> User:
        user.token_version += 1
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def email_exists(self, email: str) -> bool:
        result = await self.session.execute(
            select(func.count(User.id))
            .where(User.email == email)
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one() > 0

    async def count_admins(self) -> int:
        result = await self.session.execute(
            select(func.count(User.id))
            .where(User.role == UserRole.ADMIN)
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one()
