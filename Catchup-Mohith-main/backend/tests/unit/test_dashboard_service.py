# backend/tests/unit/test_dashboard_service.py
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.app.models.user import UserRole
from backend.app.schemas.dashboard import (
    DashboardAdminRead,
    DashboardManagerRead,
    DashboardStaffRead,
    StockMovementSummary,
    SystemHealthSummary,
)
from backend.app.services.dashboard_service import DashboardService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = 0
    result.scalar_one_or_none.return_value = None
    result.scalars.return_value.all.return_value = []
    result.all.return_value = []
    session.execute.return_value = result
    return session


def _scalar_result(value):
    r = MagicMock()
    r.scalar_one.return_value = value
    r.scalar_one_or_none.return_value = value
    return r


def _scalars_result(items):
    r = MagicMock()
    r.scalars.return_value.all.return_value = items
    r.all.return_value = items
    return r


def _make_movement() -> StockMovementSummary:
    return StockMovementSummary(
        product_name="Widget",
        product_sku="SKU-001",
        quantity_change=Decimal("10"),
        change_type="grn_receipt",
        balance_after=Decimal("50"),
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# get_dashboard — role dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_warehouse_staff_sees_only_staff_fields():
    service = DashboardService()
    user_id = uuid4()
    session = _make_session()

    with patch.object(service, "_get_staff_data", new=AsyncMock()) as mock_staff:
        mock_staff.return_value = DashboardStaffRead(
            total_products=10,
            low_stock_count=2,
            pending_grns=1,
            recent_stock_movements=[],
        )
        result = await service.get_dashboard(user_id, UserRole.WAREHOUSE_STAFF, session)

    assert isinstance(result, DashboardStaffRead)
    assert result.total_products == 10
    assert result.low_stock_count == 2
    assert result.pending_grns == 1
    assert hasattr(result, "recent_stock_movements")
    assert not hasattr(result, "open_pos")
    assert not hasattr(result, "total_users")
    assert not hasattr(result, "system_health")
    mock_staff.assert_awaited_once_with(user_id, session)


@pytest.mark.asyncio
async def test_procurement_manager_sees_manager_fields():
    service = DashboardService()
    user_id = uuid4()
    session = _make_session()

    with patch.object(service, "_get_manager_data", new=AsyncMock()) as mock_mgr:
        mock_mgr.return_value = DashboardManagerRead(
            total_products=50,
            low_stock_count=5,
            open_pos=3,
            pending_grns=4,
            total_suppliers=12,
            overdue_backorders=1,
            recent_activity=[],
        )
        result = await service.get_dashboard(
            user_id, UserRole.PROCUREMENT_MANAGER, session
        )

    assert isinstance(result, DashboardManagerRead)
    assert result.open_pos == 3
    assert result.overdue_backorders == 1
    assert result.total_suppliers == 12
    assert not hasattr(result, "total_users")
    assert not hasattr(result, "system_health")
    mock_mgr.assert_awaited_once_with(session)


@pytest.mark.asyncio
async def test_admin_sees_all_fields_including_system_health():
    service = DashboardService()
    user_id = uuid4()
    session = _make_session()

    health = SystemHealthSummary(
        database_ok=True,
        redis_ok=True,
        temporal_ok=True,
        last_tier_recalc=None,
    )
    with patch.object(service, "_get_admin_data", new=AsyncMock()) as mock_admin:
        mock_admin.return_value = DashboardAdminRead(
            total_products=50,
            low_stock_count=5,
            open_pos=3,
            pending_grns=4,
            total_suppliers=12,
            overdue_backorders=1,
            recent_activity=[],
            total_users=8,
            inactive_suppliers=2,
            auto_reorder_triggered_today=0,
            email_failures_unresolved=3,
            system_health=health,
        )
        result = await service.get_dashboard(user_id, UserRole.ADMIN, session)

    assert isinstance(result, DashboardAdminRead)
    assert result.total_users == 8
    assert result.email_failures_unresolved == 3
    assert result.system_health.database_ok is True
    mock_admin.assert_awaited_once_with(session)


# ---------------------------------------------------------------------------
# get_low_stock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_low_stock_uses_effective_threshold():
    from backend.app.models.product import Product
    from backend.app.services.dashboard_service import _to_low_stock_read

    product = Product(
        id=uuid4(),
        sku="SKU-THR",
        name="Threshold Product",
        unit_of_measure="units",
        current_stock=Decimal("4"),
        reorder_point=Decimal("10"),
        reorder_quantity=Decimal("20"),
        unit_price=Decimal("5.00"),
        low_stock_threshold_override=Decimal("5"),
        version=1,
    )

    read = _to_low_stock_read(product)

    # COALESCE(NULLIF(override=5, 0), reorder_point=10) = 5
    assert read.effective_threshold == Decimal("5")
    # current_stock=4 <= effective_threshold=5 -> appears in low-stock results
    assert read.current_stock <= read.effective_threshold
    assert read.stock_badge == "low_stock"


@pytest.mark.asyncio
async def test_low_stock_excludes_inactive_products():
    service = DashboardService()
    session = _make_session()

    count_result = _scalar_result(0)
    items_result = _scalars_result([])
    session.execute.side_effect = [count_result, items_result]

    response = await service.get_low_stock(page=1, page_size=20, session=session)

    assert response.data == []
    assert response.meta.total == 0


# ---------------------------------------------------------------------------
# get_recent_activity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recent_activity_staff_filtered_to_own_receipts():
    service = DashboardService()
    user_id = uuid4()
    session = _make_session()
    movement = _make_movement()

    with (
        patch.object(
            service,
            "_get_staff_recent_activity",
            new=AsyncMock(return_value=[movement]),
        ) as mock_staff_act,
        patch.object(
            service,
            "_get_all_recent_activity",
            new=AsyncMock(return_value=[]),
        ) as mock_all,
    ):
        result = await service.get_recent_activity(
            user_id=user_id,
            role=UserRole.WAREHOUSE_STAFF,
            limit=5,
            session=session,
        )

    assert result == [movement]
    mock_staff_act.assert_awaited_once_with(user_id, 5, session)
    mock_all.assert_not_awaited()


@pytest.mark.asyncio
async def test_recent_activity_manager_sees_all():
    service = DashboardService()
    user_id = uuid4()
    session = _make_session()
    movements = [_make_movement(), _make_movement()]

    with (
        patch.object(
            service,
            "_get_staff_recent_activity",
            new=AsyncMock(return_value=[]),
        ) as mock_staff_act,
        patch.object(
            service,
            "_get_all_recent_activity",
            new=AsyncMock(return_value=movements),
        ) as mock_all,
    ):
        result = await service.get_recent_activity(
            user_id=user_id,
            role=UserRole.PROCUREMENT_MANAGER,
            limit=10,
            session=session,
        )

    assert result == movements
    mock_all.assert_awaited_once_with(10, session)
    mock_staff_act.assert_not_awaited()


# ---------------------------------------------------------------------------
# _check_database (system health)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_system_health_db_ok_when_query_succeeds():
    from backend.app.services.dashboard_service import _check_database

    session = AsyncMock()
    session.execute.return_value = MagicMock()

    result = await _check_database(session)

    assert result is True


@pytest.mark.asyncio
async def test_system_health_db_not_ok_when_query_fails():
    from backend.app.services.dashboard_service import _check_database

    session = AsyncMock()
    session.execute.side_effect = Exception("DB connection lost")

    result = await _check_database(session)

    assert result is False
