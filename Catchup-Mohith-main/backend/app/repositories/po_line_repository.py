# /home/mohith/Catchup-Mohith/backend/app/repositories/po_line_repository.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.po_line import POLine
from backend.app.repositories.base_repository import BaseRepository


class POLineRepository(BaseRepository[POLine]):
    def __init__(self, session: AsyncSession):
        super().__init__(POLine, session)

    async def list_by_po_id(self, po_id: UUID) -> list[POLine]:
        result = await self.session.execute(
            select(POLine)
            .where(POLine.po_id == po_id)
            .order_by(POLine.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_po_id_product_id(
        self,
        po_id: UUID,
        product_id: UUID,
    ) -> POLine | None:
        result = await self.session.execute(
            select(POLine)
            .where(POLine.po_id == po_id)
            .where(POLine.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def delete_by_po_id(self, po_id: UUID) -> None:
        lines = await self.list_by_po_id(po_id)
        for line in lines:
            await self.session.delete(line)
        await self.session.flush()
