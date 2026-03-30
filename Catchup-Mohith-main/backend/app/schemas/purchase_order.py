# /home/mohith/Catchup-Mohith/backend/app/schemas/purchase_order.py
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

POStatus = Literal[
    "draft",
    "submitted",
    "acknowledged",
    "shipped",
    "received",
    "closed",
    "cancelled",
]


class POLineCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: UUID
    quantity_ordered: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)


class POLineUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID | None = None
    product_id: UUID
    quantity_ordered: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)


class POLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_id: UUID
    product_id: UUID
    quantity_ordered: Decimal
    quantity_received: Decimal
    unit_price: Decimal
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class POCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    supplier_id: UUID
    notes: str | None = None
    expected_delivery_date: date | None = None
    lines: list[POLineCreate]

    @field_validator("lines")
    @classmethod
    def validate_non_empty_lines(cls, value: list[POLineCreate]) -> list[POLineCreate]:
        if not value:
            raise ValueError("At least one PO line is required")
        return value


class POUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    notes: str | None = None
    expected_delivery_date: date | None = None
    lines: list[POLineUpdate]

    @field_validator("lines")
    @classmethod
    def validate_non_empty_lines(cls, value: list[POLineUpdate]) -> list[POLineUpdate]:
        if not value:
            raise ValueError("At least one PO line is required")
        return value


class PORead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_number: str
    supplier_id: UUID
    created_by: UUID
    status: POStatus
    total_amount: Decimal
    notes: str | None
    expected_delivery_date: date | None
    submitted_at: datetime | None
    acknowledged_at: datetime | None
    shipped_at: datetime | None
    received_at: datetime | None
    closed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    lines: list[POLineRead]


class POListParams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)
    status: POStatus | None = None
    supplier_id: UUID | None = None
    created_by_me: bool = False
