# backend/app/repositories/backorder_repository.py
from backend.app.models.backorder import Backorder
from backend.app.repositories.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID


class BackorderRepository(BaseRepository[Backorder]):
    def __init__(self, session: AsyncSession):
        super().__init__(Backorder, session)

    async def get_open_backorders_for_po(self, original_po_id: UUID) -> list[Backorder]:
        result = await self.session.execute(
            select(Backorder)
            .where(Backorder.original_po_id == original_po_id)
            .where(Backorder.status == "open")
            .order_by(Backorder.created_at.asc())
        )
        return list(result.scalars().all())

    async def create_backorder(self, backorder: Backorder) -> Backorder:
        return await self.create(backorder)
