# /home/mohith/Catchup-Mohith/backend/app/models/product.py
from decimal import Decimal

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(50), nullable=False)
    current_stock: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        server_default="0",
    )
    reorder_point: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        server_default="0",
    )
    reorder_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        server_default="0",
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    low_stock_threshold_override: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        default=1,
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku={self.sku} stock={self.current_stock}>"
