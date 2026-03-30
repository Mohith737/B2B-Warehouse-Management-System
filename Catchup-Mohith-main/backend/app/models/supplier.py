# backend/app/models/supplier.py
from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Supplier(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="30"
    )
    lead_time_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="7"
    )
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )
    current_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="'Silver'", default="Silver"
    )
    tier_locked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    consecutive_on_time: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    consecutive_late: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} name={self.name} tier={self.current_tier}>"
