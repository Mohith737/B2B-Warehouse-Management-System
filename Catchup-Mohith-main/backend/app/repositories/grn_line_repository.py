# backend/app/repositories/grn_line_repository.py
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.grn import GRN
from backend.app.models.grn_line import GRNLine
from backend.app.models.po_line import POLine
from backend.app.repositories.base_repository import BaseRepository


class GRNLineRepository(BaseRepository[GRNLine]):
    def __init__(self, session: AsyncSession):
        super().__init__(GRNLine, session)

    async def get_lines_for_grn(self, grn_id: UUID) -> list[GRNLine]:
        result = await self.session.execute(
            select(GRNLine)
            .where(GRNLine.grn_id == grn_id)
            .order_by(GRNLine.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_grn_and_product(
        self,
        grn_id: UUID,
        product_id: UUID,
    ) -> GRNLine | None:
        result = await self.session.execute(
            select(GRNLine)
            .where(GRNLine.grn_id == grn_id)
            .where(GRNLine.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_total_received_for_po_line(self, po_line_id: UUID) -> Decimal:
        po_line_result = await self.session.execute(
            select(POLine.po_id, POLine.product_id).where(POLine.id == po_line_id)
        )
        po_line = po_line_result.one_or_none()
        if po_line is None:
            return Decimal("0")

        po_id, product_id = po_line
        total_result = await self.session.execute(
            select(func.coalesce(func.sum(GRNLine.quantity_received), 0))
            .select_from(GRNLine)
            .join(GRN, GRN.id == GRNLine.grn_id)
            .where(GRN.po_id == po_id)
            .where(GRNLine.product_id == product_id)
        )
        total = total_result.scalar_one()
        return Decimal(str(total))
