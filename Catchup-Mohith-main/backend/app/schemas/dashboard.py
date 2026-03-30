# backend/app/schemas/dashboard.py
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StockMovementSummary(BaseModel):
    product_name: str
    product_sku: str
    quantity_change: Decimal
    change_type: str
    balance_after: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemHealthSummary(BaseModel):
    database_ok: bool
    redis_ok: bool
    temporal_ok: bool
    last_tier_recalc: datetime | None

    model_config = ConfigDict(from_attributes=True)


class LowStockProductRead(BaseModel):
    id: UUID
    name: str
    sku: str
    current_stock: Decimal
    reorder_point: Decimal
    low_stock_threshold_override: Decimal | None
    effective_threshold: Decimal
    stock_badge: str
    preferred_supplier_name: str | None

    model_config = ConfigDict(from_attributes=True)


class DashboardStaffRead(BaseModel):
    total_products: int
    low_stock_count: int
    pending_grns: int
    recent_stock_movements: list[StockMovementSummary]

    model_config = ConfigDict(from_attributes=True)


class DashboardManagerRead(BaseModel):
    total_products: int
    low_stock_count: int
    open_pos: int
    pending_grns: int
    total_suppliers: int
    overdue_backorders: int
    recent_activity: list[StockMovementSummary]

    model_config = ConfigDict(from_attributes=True)


class DashboardAdminRead(BaseModel):
    total_products: int
    low_stock_count: int
    open_pos: int
    pending_grns: int
    total_suppliers: int
    overdue_backorders: int
    recent_activity: list[StockMovementSummary]
    total_users: int
    inactive_suppliers: int
    auto_reorder_triggered_today: int
    email_failures_unresolved: int
    system_health: SystemHealthSummary

    model_config = ConfigDict(from_attributes=True)


# Union type used in router — resolved at service layer by role
DashboardRead = DashboardStaffRead | DashboardManagerRead | DashboardAdminRead
