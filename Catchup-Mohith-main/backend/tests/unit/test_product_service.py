# /home/mohith/Catchup-Mohith/backend/tests/unit/test_product_service.py
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from backend.app.core.exceptions import (
    BarcodeNotFoundException,
    ConflictException,
    NotFoundException,
)
from backend.app.models.product import Product
from backend.app.schemas.product import (
    ProductCreate,
    ProductUpdate,
)
from backend.app.services.product_service import (
    ProductService,
    compute_stock_badge,
)


def make_product(
    current_stock=Decimal("10"),
    reorder_point=Decimal("5"),
    low_stock_threshold_override=None,
    version=1,
    deleted_at=None,
    barcode=None,
) -> MagicMock:
    p = MagicMock(spec=Product)
    p.id = uuid4()
    p.sku = "SKU-001"
    p.name = "Test Product"
    p.description = None
    p.unit_of_measure = "units"
    p.current_stock = current_stock
    p.reorder_point = reorder_point
    p.reorder_quantity = Decimal("20")
    p.unit_price = Decimal("9.99")
    p.barcode = barcode
    p.low_stock_threshold_override = low_stock_threshold_override
    p.version = version
    p.deleted_at = deleted_at
    p.created_at = __import__("datetime").datetime.utcnow()
    p.updated_at = __import__("datetime").datetime.utcnow()
    return p


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
    repo.get_by_id_for_update = AsyncMock()
    repo.get_by_sku = AsyncMock()
    repo.get_by_barcode = AsyncMock()
    repo.sku_exists = AsyncMock(return_value=False)
    repo.barcode_exists = AsyncMock(return_value=False)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.list_with_filters = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def service(mock_session, mock_repo):
    svc = ProductService(mock_session)
    svc.repo = mock_repo
    return svc


def test_compute_stock_badge_out_of_stock_when_zero():
    badge = compute_stock_badge(
        current_stock=Decimal("0"),
        reorder_point=Decimal("5"),
        low_stock_threshold_override=None,
    )
    assert badge == "out_of_stock"


def test_compute_stock_badge_low_stock_at_reorder_point():
    badge = compute_stock_badge(
        current_stock=Decimal("5"),
        reorder_point=Decimal("5"),
        low_stock_threshold_override=None,
    )
    assert badge == "low_stock"


def test_compute_stock_badge_low_stock_uses_override_when_set():
    badge = compute_stock_badge(
        current_stock=Decimal("7"),
        reorder_point=Decimal("5"),
        low_stock_threshold_override=Decimal("10"),
    )
    assert badge == "low_stock"


def test_compute_stock_badge_in_stock_above_threshold():
    badge = compute_stock_badge(
        current_stock=Decimal("20"),
        reorder_point=Decimal("5"),
        low_stock_threshold_override=None,
    )
    assert badge == "in_stock"


def test_compute_stock_badge_zero_reorder_point_only_out_of_stock():
    badge = compute_stock_badge(
        current_stock=Decimal("1"),
        reorder_point=Decimal("0"),
        low_stock_threshold_override=None,
    )
    assert badge == "in_stock"


@pytest.mark.asyncio
async def test_create_product_raises_conflict_on_duplicate_sku(service, mock_repo):
    mock_repo.sku_exists.return_value = True
    data = ProductCreate(
        sku="DUPE-SKU",
        name="Test",
        unit_of_measure="units",
        unit_price=Decimal("10"),
    )
    with pytest.raises(ConflictException) as exc_info:
        await service.create_product(data)
    assert exc_info.value.details["field"] == "sku"


@pytest.mark.asyncio
async def test_create_product_raises_conflict_on_duplicate_barcode(service, mock_repo):
    mock_repo.sku_exists.return_value = False
    mock_repo.barcode_exists.return_value = True
    data = ProductCreate(
        sku="NEW-SKU",
        name="Test",
        unit_of_measure="units",
        unit_price=Decimal("10"),
        barcode="DUPE-BARCODE",
    )
    with pytest.raises(ConflictException) as exc_info:
        await service.create_product(data)
    assert exc_info.value.details["field"] == "barcode"


@pytest.mark.asyncio
async def test_update_product_raises_conflict_on_version_mismatch(service, mock_repo):
    product = make_product(version=3)
    mock_repo.get_by_id_for_update.return_value = product
    data = ProductUpdate(version=1)
    with pytest.raises(ConflictException) as exc_info:
        await service.update_product(product.id, data)
    assert exc_info.value.details["current_version"] == 3
    assert exc_info.value.details["submitted_version"] == 1


@pytest.mark.asyncio
async def test_update_product_succeeds_and_increments_version(service, mock_repo):
    product = make_product(version=2)
    updated_product = make_product(version=3)
    mock_repo.get_by_id_for_update.return_value = product
    mock_repo.update.return_value = updated_product
    data = ProductUpdate(version=2, name="Updated Name")
    result = await service.update_product(product.id, data)
    assert result.version == 3
    call_args = mock_repo.update.call_args[0][1]
    assert call_args["version"] == 3


@pytest.mark.asyncio
async def test_get_product_raises_not_found_for_missing_id(service, mock_repo):
    mock_repo.get_by_id.return_value = None
    with pytest.raises(NotFoundException):
        await service.get_product(uuid4())


@pytest.mark.asyncio
async def test_get_product_raises_not_found_for_soft_deleted(service, mock_repo):
    mock_repo.get_by_id.return_value = None
    with pytest.raises(NotFoundException):
        await service.get_product(uuid4())


@pytest.mark.asyncio
async def test_list_products_filters_by_badge_status(service, mock_repo):
    low_product = make_product(
        current_stock=Decimal("3"),
        reorder_point=Decimal("5"),
    )
    mock_repo.list_with_filters.return_value = ([low_product], 1)
    from backend.app.schemas.product import ProductListParams

    params = ProductListParams(badge="low_stock")
    result = await service.list_products(params)
    assert result.meta.total == 1
    mock_repo.list_with_filters.assert_called_once_with(
        search=None,
        badge="low_stock",
        skip=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_list_products_search_matches_name_and_sku(service, mock_repo):
    product = make_product()
    mock_repo.list_with_filters.return_value = ([product], 1)
    from backend.app.schemas.product import ProductListParams

    params = ProductListParams(search="widget")
    await service.list_products(params)
    mock_repo.list_with_filters.assert_called_once_with(
        search="widget",
        badge=None,
        skip=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_delete_product_sets_deleted_at(service, mock_repo):
    product = make_product()
    mock_repo.get_by_id.return_value = product
    mock_repo.soft_delete.return_value = product
    await service.delete_product(product.id)
    mock_repo.soft_delete.assert_called_once_with(product)


@pytest.mark.asyncio
async def test_barcode_lookup_raises_barcode_not_found(service, mock_repo):
    mock_repo.get_by_barcode.return_value = None
    with pytest.raises(BarcodeNotFoundException) as exc_info:
        await service.barcode_lookup("UNKNOWN-BARCODE")
    assert exc_info.value.details["barcode"] == "UNKNOWN-BARCODE"
