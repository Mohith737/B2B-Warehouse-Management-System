# backend/app/models/supplier_metrics_history.py
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.supplier import Supplier


class SupplierMetricsHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "supplier_metrics_history"

    __table_args__ = (
        UniqueConstraint(
            "supplier_id",
            "period_year",
            "period_month",
            name="uq_supplier_metrics_period",
        ),
    )

    supplier_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    total_pos: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    on_time_deliveries: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    total_po_lines: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    defect_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    avg_fulfilment_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default="0"
    )
    computed_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    tier_at_period_end: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    supplier: Mapped["Supplier"] = relationship("Supplier")

    def __repr__(self) -> str:
        return (
            f"<SupplierMetricsHistory "
            f"supplier_id={self.supplier_id} "
            f"period={self.period_year}-{self.period_month}>"
        )
