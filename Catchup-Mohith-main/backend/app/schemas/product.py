# /home/mohith/Catchup-Mohith/backend/app/schemas/product.py
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

StockBadge = Literal["out_of_stock", "low_stock", "in_stock"]


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    unit_of_measure: str = Field(..., min_length=1, max_length=50)
    reorder_point: Decimal = Field(default=Decimal("0"), ge=0)
    reorder_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    unit_price: Decimal = Field(..., gt=0)
    barcode: str | None = Field(default=None, max_length=100)
    low_stock_threshold_override: Decimal | None = Field(default=None, ge=0)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    unit_of_measure: str | None = Field(default=None, max_length=50)
    reorder_point: Decimal | None = Field(default=None, ge=0)
    reorder_quantity: Decimal | None = Field(default=None, ge=0)
    unit_price: Decimal | None = Field(default=None, gt=0)
    barcode: str | None = Field(default=None, max_length=100)
    low_stock_threshold_override: Decimal | None = Field(default=None, ge=0)
    version: int  # required — no default, always provided

    # Behaviour:
    # Fields omitted from request body -> not in model_fields_set
    #   -> not written to DB (field unchanged)
    # Fields explicitly set to null -> in model_fields_set
    #   -> DB value cleared to null
    # version always required for optimistic locking


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name: str
    description: str | None
    unit_of_measure: str
    current_stock: Decimal
    reorder_point: Decimal
    reorder_quantity: Decimal
    unit_price: Decimal
    barcode: str | None
    low_stock_threshold_override: Decimal | None
    version: int
    stock_badge: StockBadge
    created_at: datetime
    updated_at: datetime


class ProductListParams(BaseModel):
    """Query parameters for GET /products."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    search: str | None = None
    badge: StockBadge | None = None
