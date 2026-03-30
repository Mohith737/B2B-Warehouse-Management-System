# /home/mohith/Catchup-Mohith/backend/app/routers/stock_ledger.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.stock_ledger import (
    StockLedgerChangeType,
    StockLedgerCursorMeta,
    StockLedgerListResponse,
)
from backend.app.services.stock_ledger_service import StockLedgerService

router = APIRouter()


@router.get(
    "/",
    response_model=StockLedgerListResponse,
    summary="List stock ledger entries with cursor pagination",
)
async def list_stock_ledger(
    product_id: UUID | None = Query(default=None),
    change_type: StockLedgerChangeType | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockLedgerListResponse:
    service = StockLedgerService()
    items, next_cursor = await service.get_page(
        session=session,
        product_id=product_id,
        change_type=change_type,
        cursor=cursor,
        limit=limit,
    )
    return StockLedgerListResponse(
        data=items,
        meta=StockLedgerCursorMeta(limit=limit, next_cursor=next_cursor),
    )
