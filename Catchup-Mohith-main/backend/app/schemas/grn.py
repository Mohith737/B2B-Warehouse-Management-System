# backend/app/schemas/grn.py
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

GRNStatus = Literal["open", "completed"]


class GRNCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    po_id: UUID


class GRNLineCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: UUID
    quantity_received: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(..., gt=0)
    barcode_scanned: str | None = Field(default=None, max_length=100)


class GRNLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grn_id: UUID
    product_id: UUID
    quantity_received: Decimal
    unit_cost: Decimal
    barcode_scanned: str | None
    created_at: datetime
    updated_at: datetime


class GRNRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_id: UUID
    status: GRNStatus
    completed_at: datetime | None
    auto_reorder_triggered: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    lines: list[GRNLineRead]


class GRNListParams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    po_id: UUID | None = None
    status: GRNStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)
