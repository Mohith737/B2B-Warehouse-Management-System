# backend/app/models/backorder.py
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BackorderStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class Backorder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "backorders"

    original_po_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    quantity_outstanding: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BackorderStatus.OPEN.value,
        server_default="'open'",
    )
    grn_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("grns.id"),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Backorder id={self.id} po_id={self.original_po_id} "
            f"product_id={self.product_id} status={self.status}>"
        )
