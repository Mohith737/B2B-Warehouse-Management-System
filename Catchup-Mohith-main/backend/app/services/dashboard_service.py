# backend/app/services/dashboard_service.py
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    ServiceUnavailableException,
    StockBridgeException,
)
from backend.app.models.email_failure_log import EmailFailureLog
from backend.app.models.grn import GRN, GRNStatus
from backend.app.models.product import Product
from backend.app.models.purchase_order import PurchaseOrder, POStatus
from backend.app.models.stock_ledger import StockLedger
from backend.app.models.supplier import Supplier
from backend.app.models.supplier_metrics_history import SupplierMetricsHistory
from backend.app.models.user import User, UserRole
from backend.app.schemas.common import ListResponse, make_pagination_meta
from backend.app.schemas.dashboard import (
    DashboardAdminRead,
    DashboardManagerRead,
    DashboardStaffRead,
    LowStockProductRead,
    StockMovementSummary,
    SystemHealthSummary,
)

logger = logging.getLogger(__name__)

# Effective threshold: COALESCE(NULLIF(low_stock_threshold_override, 0), reorder_point)
_EFFECTIVE_THRESHOLD_EXPR = func.coalesce(
    func.nullif(Product.low_stock_threshold_override, 0),
    Product.reorder_point,
)

_OPEN_PO_STATUSES = (POStatus.SUBMITTED.value, POStatus.ACKNOWLEDGED.value)


class DashboardService:
    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    async def get_dashboard(
        self,
        user_id: UUID,
        role: UserRole,
        session: AsyncSession,
    ) -> DashboardStaffRead | DashboardManagerRead | DashboardAdminRead:
        try:
            if role == UserRole.WAREHOUSE_STAFF:
                return await self._get_staff_data(user_id, session)
            if role == UserRole.PROCUREMENT_MANAGER:
                return await self._get_manager_data(session)
            # ADMIN
            return await self._get_admin_data(session)
        except StockBridgeException:
            raise
        except Exception as exc:
            logger.error("Dashboard query failed: %s", exc, exc_info=True)
            raise ServiceUnavailableException(details={"error": str(exc)}) from exc

    async def get_low_stock(
        self,
        page: int,
        page_size: int,
        session: AsyncSession,
    ) -> ListResponse[LowStockProductRead]:
        effective = _EFFECTIVE_THRESHOLD_EXPR

        base_where = (
            Product.deleted_at.is_(None),
            Product.current_stock <= effective,
        )

        count_result = await session.execute(
            select(func.count(Product.id)).where(*base_where)
        )
        total: int = count_result.scalar_one()

        rows_result = await session.execute(
            select(Product)
            .where(*base_where)
            .order_by(Product.current_stock.asc(), Product.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        products = list(rows_result.scalars().all())

        items = [_to_low_stock_read(p) for p in products]
        return ListResponse(
            data=items,
            meta=make_pagination_meta(total, page, page_size),
        )

    async def get_recent_activity(
        self,
        user_id: UUID,
        role: UserRole,
        limit: int,
        session: AsyncSession,
    ) -> list[StockMovementSummary]:
        if role == UserRole.WAREHOUSE_STAFF:
            return await self._get_staff_recent_activity(user_id, limit, session)
        return await self._get_all_recent_activity(limit, session)

    # ------------------------------------------------------------------
    # Role-specific dashboard builders
    # ------------------------------------------------------------------

    async def _get_staff_data(
        self,
        user_id: UUID,
        session: AsyncSession,
    ) -> DashboardStaffRead:
        total_products = await _count_active_products(session)
        low_stock_count = await _count_low_stock(session)
        pending_grns = await _count_open_grns_for_user(user_id, session)
        recent_stock_movements = await self._get_staff_recent_activity(
            user_id, 5, session
        )
        return DashboardStaffRead(
            total_products=total_products,
            low_stock_count=low_stock_count,
            pending_grns=pending_grns,
            recent_stock_movements=recent_stock_movements,
        )

    async def _get_manager_data(
        self,
        session: AsyncSession,
    ) -> DashboardManagerRead:
        total_products = await _count_active_products(session)
        low_stock_count = await _count_low_stock(session)
        open_pos = await _count_open_pos(session)
        pending_grns = await _count_all_open_grns(session)
        total_suppliers = await _count_active_suppliers(session)
        overdue_backorders = await _count_overdue_backorders(session)
        recent_activity = await self._get_all_recent_activity(10, session)
        return DashboardManagerRead(
            total_products=total_products,
            low_stock_count=low_stock_count,
            open_pos=open_pos,
            pending_grns=pending_grns,
            total_suppliers=total_suppliers,
            overdue_backorders=overdue_backorders,
            recent_activity=recent_activity,
        )

    async def _get_admin_data(
        self,
        session: AsyncSession,
    ) -> DashboardAdminRead:
        manager_data = await self._get_manager_data(session)

        total_users = await _count_all_users(session)
        inactive_suppliers = await _count_inactive_suppliers(session)
        auto_reorder_today = await _count_auto_reorder_triggered_today(session)
        email_failures = await _count_unresolved_email_failures(session)
        system_health = await self._get_system_health(session)

        return DashboardAdminRead(
            total_products=manager_data.total_products,
            low_stock_count=manager_data.low_stock_count,
            open_pos=manager_data.open_pos,
            pending_grns=manager_data.pending_grns,
            total_suppliers=manager_data.total_suppliers,
            overdue_backorders=manager_data.overdue_backorders,
            recent_activity=manager_data.recent_activity,
            total_users=total_users,
            inactive_suppliers=inactive_suppliers,
            auto_reorder_triggered_today=auto_reorder_today,
            email_failures_unresolved=email_failures,
            system_health=system_health,
        )

    async def _get_system_health(
        self,
        session: AsyncSession,
    ) -> SystemHealthSummary:
        database_ok = await _check_database(session)
        redis_ok = await _check_redis()
        temporal_ok = await self._check_temporal()
        last_tier_recalc = await _get_last_tier_recalc(session)

        return SystemHealthSummary(
            database_ok=database_ok,
            redis_ok=redis_ok,
            temporal_ok=temporal_ok,
            last_tier_recalc=last_tier_recalc,
        )

    async def _check_temporal(self) -> bool:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    settings.temporal_host,
                    settings.temporal_port,
                ),
                timeout=2.0,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Activity helpers
    # ------------------------------------------------------------------

    async def _get_staff_recent_activity(
        self,
        user_id: UUID,
        limit: int,
        session: AsyncSession,
    ) -> list[StockMovementSummary]:
        # Staff see ledger entries for products they have receipted.
        # GRNs created by this user record stock via StockLedger with
        # change_type='grn_receipt' and reference_id=grn.id.
        # Subquery: GRN ids created by this user.
        grn_id_subq = select(GRN.id).where(GRN.created_by == user_id).scalar_subquery()
        stmt = (
            select(StockLedger, Product.name.label("product_name"), Product.sku)
            .join(Product, Product.id == StockLedger.product_id)
            .where(StockLedger.reference_id.in_(grn_id_subq))
            .order_by(StockLedger.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [
            StockMovementSummary(
                product_name=row.product_name,
                product_sku=row.sku,
                quantity_change=row.StockLedger.quantity_change,
                change_type=row.StockLedger.change_type,
                balance_after=row.StockLedger.balance_after,
                created_at=row.StockLedger.created_at,
            )
            for row in result.all()
        ]

    async def _get_all_recent_activity(
        self,
        limit: int,
        session: AsyncSession,
    ) -> list[StockMovementSummary]:
        stmt = (
            select(StockLedger, Product.name.label("product_name"), Product.sku)
            .join(Product, Product.id == StockLedger.product_id)
            .order_by(StockLedger.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [
            StockMovementSummary(
                product_name=row.product_name,
                product_sku=row.sku,
                quantity_change=row.StockLedger.quantity_change,
                change_type=row.StockLedger.change_type,
                balance_after=row.StockLedger.balance_after,
                created_at=row.StockLedger.created_at,
            )
            for row in result.all()
        ]


# ------------------------------------------------------------------
# Private module-level query helpers
# ------------------------------------------------------------------


async def _count_active_products(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(Product.id)).where(Product.deleted_at.is_(None))
    )
    return result.scalar_one()


async def _count_low_stock(session: AsyncSession) -> int:
    effective = _EFFECTIVE_THRESHOLD_EXPR
    result = await session.execute(
        select(func.count(Product.id)).where(
            Product.deleted_at.is_(None),
            Product.current_stock <= effective,
        )
    )
    return result.scalar_one()


async def _count_open_grns_for_user(user_id: UUID, session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(GRN.id)).where(
            GRN.created_by == user_id,
            GRN.status == GRNStatus.OPEN.value,
        )
    )
    return result.scalar_one()


async def _count_all_open_grns(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(GRN.id)).where(GRN.status == GRNStatus.OPEN.value)
    )
    return result.scalar_one()


async def _count_open_pos(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.deleted_at.is_(None),
            PurchaseOrder.status.in_(_OPEN_PO_STATUSES),
        )
    )
    return result.scalar_one()


async def _count_active_suppliers(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(Supplier.id)).where(
            Supplier.deleted_at.is_(None),
            Supplier.is_active.is_(True),
        )
    )
    return result.scalar_one()


async def _count_overdue_backorders(session: AsyncSession) -> int:
    # Open POs (submitted/acknowledged) created more than 7 days ago
    # are considered overdue backorders.
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    result = await session.execute(
        select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.deleted_at.is_(None),
            PurchaseOrder.status.in_(_OPEN_PO_STATUSES),
            PurchaseOrder.created_at < cutoff,
        )
    )
    return result.scalar_one()


async def _count_all_users(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(User.id)).where(User.deleted_at.is_(None))
    )
    return result.scalar_one()


async def _count_inactive_suppliers(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(Supplier.id)).where(
            Supplier.deleted_at.is_(None),
            Supplier.is_active.is_(False),
        )
    )
    return result.scalar_one()


async def _count_auto_reorder_triggered_today(session: AsyncSession) -> int:
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    result = await session.execute(
        select(func.count(GRN.id)).where(
            GRN.auto_reorder_triggered.is_(True),
            GRN.completed_at >= today_start,
        )
    )
    return result.scalar_one()


async def _count_unresolved_email_failures(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(EmailFailureLog.id)).where(
            EmailFailureLog.resolved.is_(False)
        )
    )
    return result.scalar_one()


async def _check_database(session: AsyncSession) -> bool:
    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await client.ping()
        await client.aclose()
        return True
    except Exception:
        return False


async def _get_last_tier_recalc(session: AsyncSession) -> datetime | None:
    result = await session.execute(select(func.max(SupplierMetricsHistory.created_at)))
    value = result.scalar_one_or_none()
    return value


# ------------------------------------------------------------------
# Schema conversion helpers
# ------------------------------------------------------------------


def _to_low_stock_read(product: Product) -> LowStockProductRead:
    override = product.low_stock_threshold_override
    reorder = product.reorder_point
    # COALESCE(NULLIF(override, 0), reorder_point)
    if override is not None and override != Decimal("0"):
        effective = override
    else:
        effective = reorder

    if product.current_stock <= Decimal("0"):
        badge = "out_of_stock"
    else:
        badge = "low_stock"

    return LowStockProductRead(
        id=product.id,
        name=product.name,
        sku=product.sku,
        current_stock=product.current_stock,
        reorder_point=reorder,
        low_stock_threshold_override=override,
        effective_threshold=effective,
        stock_badge=badge,
        preferred_supplier_name=None,  # no preferred_supplier FK on Product model
    )
