# backend/app/models/stock_ledger.py
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, UUIDPrimaryKeyMixin


class StockLedgerChangeType(str, Enum):
    GRN_RECEIPT = "grn_receipt"
    PO_RESERVATION = "po_reservation"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    REORDER_AUTO = "reorder_auto"
    BACKORDER_FULFILLMENT = "backorder_fulfillment"


class StockLedger(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "stock_ledger"

    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    change_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    reference_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<StockLedger id={self.id} product_id={self.product_id} "
            f"change={self.quantity_change}>"
        )
