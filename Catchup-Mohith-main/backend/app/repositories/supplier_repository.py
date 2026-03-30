# backend/app/repositories/supplier_repository.py
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.supplier import Supplier
from backend.app.repositories.base_repository import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, session: AsyncSession):
        super().__init__(Supplier, session)

    async def get_by_email(self, email: str) -> Supplier | None:
        result = await self.session.execute(
            select(Supplier)
            .where(Supplier.email == email)
            .where(Supplier.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        result = await self.session.execute(
            select(func.count(Supplier.id))
            .where(Supplier.email == email)
            .where(Supplier.deleted_at.is_(None))
        )
        return result.scalar_one() > 0

    async def list_with_filters(
        self,
        search: str | None = None,
        tier: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Supplier], int]:
        base_query = select(Supplier).where(Supplier.deleted_at.is_(None))

        if search:
            base_query = base_query.where(Supplier.name.ilike(f"%{search}%"))

        if tier is not None:
            base_query = base_query.where(Supplier.current_tier == tier)

        if is_active is not None:
            base_query = base_query.where(and_(Supplier.is_active.is_(is_active)))

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        data_query = base_query.order_by(Supplier.name.asc()).offset(skip).limit(limit)
        result = await self.session.execute(data_query)
        items = list(result.scalars().all())
        return items, total
