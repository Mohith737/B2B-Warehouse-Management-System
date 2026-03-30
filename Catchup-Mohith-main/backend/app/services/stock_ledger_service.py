# backend/app/services/stock_ledger_service.py
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    InvalidCursorException,
    InsufficientStockException,
    NotFoundException,
)
from backend.app.models.stock_ledger import StockLedger
from backend.app.repositories.product_repository import ProductRepository
from backend.app.repositories.stock_ledger_repository import StockLedgerRepository
from backend.app.schemas.stock_ledger import StockLedgerRead


class StockLedgerService:
    async def add_entry(
        self,
        session: AsyncSession,
        product_id: UUID,
        quantity_change: Decimal,
        change_type: str,
        reference_id: UUID | None,
        notes: str | None,
    ) -> StockLedgerRead:
        product_repo = ProductRepository(session)
        ledger_repo = StockLedgerRepository(session)

        product = await product_repo.get_by_id_for_update(product_id)
        if product is None:
            raise NotFoundException(message=f"Product with id={product_id} not found")

        current_stock = Decimal(str(product.current_stock))
        delta = Decimal(str(quantity_change))
        new_stock = current_stock + delta

        if new_stock < 0:
            raise InsufficientStockException(
                details={
                    "product_id": str(product_id),
                    "current_stock": str(current_stock),
                    "quantity_change": str(delta),
                }
            )

        product.current_stock = new_stock

        entry = StockLedger(
            product_id=product_id,
            quantity_change=delta,
            change_type=change_type,
            reference_id=reference_id,
            notes=notes,
            balance_after=new_stock,
        )
        created = await ledger_repo.create(entry)

        # Flush only. Caller owns transaction boundaries.
        await session.flush()
        return StockLedgerRead.model_validate(created)

    async def get_page(
        self,
        session: AsyncSession,
        product_id: UUID | None = None,
        change_type: str | None = None,
        cursor: str | UUID | None = None,
        limit: int = 20,
    ) -> tuple[list[StockLedgerRead], UUID | None]:
        ledger_repo = StockLedgerRepository(session)

        parsed_cursor: UUID | None = None
        if cursor is not None:
            if isinstance(cursor, UUID):
                parsed_cursor = cursor
            else:
                try:
                    parsed_cursor = UUID(str(cursor))
                except ValueError as exc:
                    raise InvalidCursorException(
                        details={"cursor": str(cursor)}
                    ) from exc

        items, next_cursor = await ledger_repo.get_page_with_cursor(
            product_id=product_id,
            change_type=change_type,
            cursor=parsed_cursor,
            limit=limit,
        )
        return [StockLedgerRead.model_validate(item) for item in items], next_cursor
