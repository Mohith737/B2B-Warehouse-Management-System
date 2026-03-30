# backend/app/schemas/supplier.py
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SupplierCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    payment_terms_days: int = Field(default=30, ge=1, le=365)
    lead_time_days: int = Field(default=7, ge=1, le=365)
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0)


class SupplierUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    payment_terms_days: int | None = Field(default=None, ge=1, le=365)
    lead_time_days: int | None = Field(default=None, ge=1, le=365)
    credit_limit: Decimal | None = Field(default=None, ge=0)


class TierLockRequest(BaseModel):
    tier_locked: bool


class SupplierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    phone: str | None
    address: str | None
    payment_terms_days: int
    lead_time_days: int
    credit_limit: Decimal
    current_tier: str
    tier_locked: bool
    consecutive_on_time: int
    consecutive_late: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SupplierMetricsHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    supplier_id: UUID
    period_year: int
    period_month: int
    total_pos: int
    on_time_deliveries: int
    total_po_lines: int
    defect_count: int
    avg_fulfilment_rate: Decimal
    computed_score: Decimal | None
    tier_at_period_end: str | None
    created_at: datetime


class SupplierListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)
    search: str | None = None
    tier: str | None = None
    is_active: bool | None = None
