# backend/app/schemas/stock_ledger.py
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

StockLedgerChangeType = Literal[
    "grn_receipt",
    "po_reservation",
    "manual_adjustment",
    "reorder_auto",
    "backorder_fulfillment",
]


class StockLedgerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    quantity_change: Decimal
    change_type: StockLedgerChangeType
    reference_id: UUID | None
    notes: str | None
    balance_after: Decimal
    created_at: datetime


class StockLedgerListParams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: UUID | None = None
    change_type: StockLedgerChangeType | None = None
    cursor: UUID | None = None
    limit: int = Field(default=20, ge=1, le=100)


class StockLedgerCursorMeta(BaseModel):
    model_config = ConfigDict(frozen=True)

    limit: int
    next_cursor: UUID | None


class StockLedgerListResponse(BaseModel):
    data: list[StockLedgerRead]
    meta: StockLedgerCursorMeta
