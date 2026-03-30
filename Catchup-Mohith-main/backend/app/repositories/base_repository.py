# /home/mohith/Catchup-Mohith/backend/app/repositories/base_repository.py
from datetime import datetime, timezone
from typing import Any, Generic, Type, TypeVar
from uuid import UUID

from backend.app.db.base import Base
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID) -> ModelType | None:
        result = await self.session.execute(
            select(self.model)
            .where(self.model.id == id)
            .where(self.model.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[ModelType], int]:
        count_result = await self.session.execute(
            select(func.count(self.model.id)).where(self.model.deleted_at.is_(None))
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(self.model)
            .where(self.model.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType, data: dict[str, Any]) -> ModelType:
        for key, value in data.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def soft_delete(self, obj: ModelType) -> ModelType:
        obj.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return obj

    async def hard_delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def exists(self, id: UUID) -> bool:
        result = await self.session.execute(
            select(func.count(self.model.id))
            .where(self.model.id == id)
            .where(self.model.deleted_at.is_(None))
        )
        return result.scalar_one() > 0
