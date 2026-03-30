# backend/app/models/grn_line.py
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GRNLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "grn_lines"

    __table_args__ = (
        UniqueConstraint("grn_id", "product_id", name="uq_grn_lines_grn_product"),
    )

    grn_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("grns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    barcode_scanned: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<GRNLine id={self.id} grn_id={self.grn_id} "
            f"product_id={self.product_id}>"
        )
