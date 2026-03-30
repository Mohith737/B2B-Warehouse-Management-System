# backend/tests/unit/test_supplier_service.py
import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from backend.app.core.exceptions import (
    ConflictException,
    NotFoundException,
)
from backend.app.models.supplier import Supplier
from backend.app.schemas.supplier import (
    SupplierCreate,
    SupplierListParams,
)
from backend.app.services.supplier_service import SupplierService


def make_supplier(
    is_active=True,
    tier_locked=False,
    current_tier="Silver",
) -> MagicMock:
    s = MagicMock(spec=Supplier)
    s.id = uuid4()
    s.name = "Test Supplier Co"
    s.email = "supplier@test.com"
    s.phone = None
    s.address = None
    s.payment_terms_days = 30
    s.lead_time_days = 7
    s.credit_limit = Decimal("50000")
    s.current_tier = current_tier
    s.tier_locked = tier_locked
    s.consecutive_on_time = 0
    s.consecutive_late = 0
    s.is_active = is_active
    s.created_at = __import__("datetime").datetime.utcnow()
    s.updated_at = __import__("datetime").datetime.utcnow()
    s.deleted_at = None
    return s


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.begin = MagicMock(
        return_value=MagicMock(
            __aenter__=AsyncMock(return_value=None),
            __aexit__=AsyncMock(return_value=False),
        )
    )
    return session


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock(return_value=None)
    repo.email_exists = AsyncMock(return_value=False)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.list_with_filters = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def mock_metrics_repo():
    repo = MagicMock()
    repo.get_last_n_months = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_session, mock_repo, mock_metrics_repo):
    svc = SupplierService(mock_session)
    svc.repo = mock_repo
    svc.metrics_repo = mock_metrics_repo
    return svc


@pytest.mark.asyncio
async def test_create_supplier_success(service, mock_repo):
    supplier = make_supplier()
    mock_repo.email_exists.return_value = False
    mock_repo.create.return_value = supplier
    data = SupplierCreate(
        name="Test Supplier",
        email="new@supplier.com",
        credit_limit=Decimal("10000"),
    )
    result = await service.create_supplier(data)
    assert result.email == supplier.email
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_supplier_duplicate_email_raises_conflict(service, mock_repo):
    mock_repo.email_exists.return_value = True
    data = SupplierCreate(
        name="Duplicate",
        email="existing@supplier.com",
    )
    with pytest.raises(ConflictException) as exc_info:
        await service.create_supplier(data)
    assert exc_info.value.details["field"] == "email"


@pytest.mark.asyncio
async def test_get_supplier_not_found_raises_not_found(service, mock_repo):
    mock_repo.get_by_id.return_value = None
    with pytest.raises(NotFoundException):
        await service.get_supplier(uuid4())


@pytest.mark.asyncio
async def test_deactivate_supplier_sets_is_active_false(service, mock_repo):
    supplier = make_supplier(is_active=True)
    deactivated = make_supplier(is_active=False)
    mock_repo.get_by_id.return_value = supplier
    mock_repo.update.return_value = deactivated
    result = await service.deactivate_supplier(supplier.id)
    assert result.is_active is False
    mock_repo.update.assert_called_once_with(supplier, {"is_active": False})


@pytest.mark.asyncio
async def test_activate_supplier_sets_is_active_true(service, mock_repo):
    supplier = make_supplier(is_active=False)
    activated = make_supplier(is_active=True)
    mock_repo.get_by_id.return_value = supplier
    mock_repo.update.return_value = activated
    result = await service.activate_supplier(supplier.id)
    assert result.is_active is True
    mock_repo.update.assert_called_once_with(supplier, {"is_active": True})


@pytest.mark.asyncio
async def test_tier_lock_sets_tier_locked_true(service, mock_repo):
    supplier = make_supplier(tier_locked=False)
    locked = make_supplier(tier_locked=True)
    mock_repo.get_by_id.return_value = supplier
    mock_repo.update.return_value = locked
    result = await service.set_tier_lock(supplier.id, True)
    assert result.tier_locked is True
    mock_repo.update.assert_called_once_with(supplier, {"tier_locked": True})


@pytest.mark.asyncio
async def test_list_suppliers_filters_by_tier(service, mock_repo):
    gold_supplier = make_supplier(current_tier="Gold")
    mock_repo.list_with_filters.return_value = ([gold_supplier], 1)
    params = SupplierListParams(tier="Gold")
    result = await service.list_suppliers(params)
    assert result.meta.total == 1
    mock_repo.list_with_filters.assert_called_once_with(
        search=None,
        tier="Gold",
        is_active=None,
        skip=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_list_suppliers_filters_by_active_status(service, mock_repo):
    inactive = make_supplier(is_active=False)
    mock_repo.list_with_filters.return_value = ([inactive], 1)
    params = SupplierListParams(is_active=False)
    result = await service.list_suppliers(params)
    assert result.meta.total == 1
    mock_repo.list_with_filters.assert_called_once_with(
        search=None,
        tier=None,
        is_active=False,
        skip=0,
        limit=20,
    )
