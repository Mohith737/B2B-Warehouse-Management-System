# backend/app/repositories/stock_ledger_repository.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.stock_ledger import StockLedger
from backend.app.repositories.base_repository import BaseRepository


class StockLedgerRepository(BaseRepository[StockLedger]):
    def __init__(self, session: AsyncSession):
        super().__init__(StockLedger, session)

    async def get_page_with_cursor(
        self,
        product_id: UUID | None = None,
        change_type: str | None = None,
        cursor: UUID | None = None,
        limit: int = 20,
    ) -> tuple[list[StockLedger], UUID | None]:
        query = select(StockLedger)

        if product_id is not None:
            query = query.where(StockLedger.product_id == product_id)

        if change_type is not None:
            query = query.where(StockLedger.change_type == change_type)

        if cursor is not None:
            query = query.where(StockLedger.id > cursor)

        query = query.order_by(StockLedger.id.asc()).limit(limit + 1)
        result = await self.session.execute(query)
        rows = list(result.scalars().all())

        if len(rows) > limit:
            next_cursor = rows[limit - 1].id
            items = rows[:limit]
        else:
            next_cursor = None
            items = rows

        return items, next_cursor
