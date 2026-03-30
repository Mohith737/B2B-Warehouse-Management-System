# backend/app/repositories/grn_repository.py
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.grn import GRN
from backend.app.models.grn_line import GRNLine
from backend.app.repositories.base_repository import BaseRepository


class GRNRepository(BaseRepository[GRN]):
    def __init__(self, session: AsyncSession):
        super().__init__(GRN, session)

    async def get_by_id_with_lines(self, id: UUID) -> GRN | None:
        result = await self.session.execute(
            select(GRN).options(selectinload("*")).where(GRN.id == id)
        )
        grn = result.scalar_one_or_none()
        if grn is None:
            return None

        lines_result = await self.session.execute(
            select(GRNLine)
            .where(GRNLine.grn_id == grn.id)
            .order_by(GRNLine.created_at.asc())
        )
        setattr(grn, "lines", list(lines_result.scalars().all()))
        return grn

    async def list_with_filters(
        self,
        po_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[GRN], int]:
        base_query = select(GRN)

        if po_id is not None:
            base_query = base_query.where(GRN.po_id == po_id)

        if status is not None:
            base_query = base_query.where(GRN.status == status)

        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        data_query = (
            base_query.order_by(GRN.created_at.desc()).offset(skip).limit(limit)
        )
        items = list((await self.session.execute(data_query)).scalars().all())
        return items, total
