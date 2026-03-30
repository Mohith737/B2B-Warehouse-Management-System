# /home/mohith/Catchup-Mohith/backend/tests/unit/test_purchase_order_service.py
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.app.core.exceptions import (
    ConflictException,
    CreditLimitExceededException,
    InvalidStateTransitionException,
    SupplierInactiveException,
)
from backend.app.models.user import UserRole
from backend.app.schemas.purchase_order import (
    POCreate,
    POListParams,
    POUpdate,
    POLineCreate,
    POLineUpdate,
)
from backend.app.services.purchase_order_service import PurchaseOrderService


class DummyLine:
    def __init__(self, po_id):
        self.id = uuid4()
        self.po_id = po_id
        self.product_id = uuid4()
        self.quantity_ordered = Decimal("2")
        self.quantity_received = Decimal("0")
        self.unit_price = Decimal("10")
        self.line_total = Decimal("20")
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class DummyPO:
    def __init__(self, status="draft"):
        self.id = uuid4()
        self.po_number = "SB-2026-000001"
        self.supplier_id = uuid4()
        self.created_by = uuid4()
        self.status = status
        self.total_amount = Decimal("20")
        self.notes = "n"
        self.expected_delivery_date = date.today()
        self.submitted_at = None
        self.acknowledged_at = None
        self.shipped_at = None
        self.received_at = None
        self.closed_at = None
        self.cancelled_at = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.lines = [DummyLine(self.id)]


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.begin = MagicMock(
        return_value=MagicMock(
            __aenter__=AsyncMock(return_value=None),
            __aexit__=AsyncMock(return_value=False),
        )
    )
    session.flush = AsyncMock()
    return session


@pytest.fixture
def service(mock_session):
    svc = PurchaseOrderService(mock_session)
    svc.po_repo = MagicMock()
    svc.po_line_repo = MagicMock()
    svc.supplier_repo = MagicMock()
    svc.product_repo = MagicMock()
    svc.po_number_service = MagicMock()

    svc.po_repo.create = AsyncMock()
    svc.po_repo.get_by_id = AsyncMock()
    svc.po_repo.get_by_id_with_lines = AsyncMock()
    svc.po_repo.get_by_id_for_update = AsyncMock()
    svc.po_repo.list_with_filters = AsyncMock(return_value=([], 0))
    svc.po_repo.get_open_exposure_for_supplier_for_update = AsyncMock(
        return_value=Decimal("0")
    )
    svc.po_repo.soft_delete = AsyncMock()

    svc.po_line_repo.create = AsyncMock()
    svc.po_line_repo.list_by_po_id = AsyncMock(return_value=[])
    svc.po_line_repo.delete_by_po_id = AsyncMock()

    svc.supplier_repo.get_by_id = AsyncMock()
    svc.product_repo.get_by_id = AsyncMock(return_value=MagicMock())
    svc.po_number_service.generate_next_po_number = AsyncMock(
        return_value="SB-2026-000001"
    )
    return svc


def _create_payload(supplier_id):
    return POCreate(
        supplier_id=supplier_id,
        notes="hello",
        lines=[
            POLineCreate(
                product_id=uuid4(),
                quantity_ordered=Decimal("2"),
                unit_price=Decimal("10"),
            )
        ],
    )


@pytest.mark.asyncio
async def test_create_po_success_returns_po_with_number(service):
    supplier = MagicMock(is_active=True)
    supplier.id = uuid4()
    po = DummyPO(status="draft")
    service.supplier_repo.get_by_id.return_value = supplier
    service.po_repo.create.return_value = po
    service.po_repo.get_by_id_with_lines.return_value = po
    service.po_line_repo.list_by_po_id.return_value = po.lines
    service.po_repo.get_by_id_for_update.return_value = po

    result = await service.create_purchase_order(
        _create_payload(supplier.id), created_by=uuid4()
    )
    assert result.po_number.startswith("SB-")


@pytest.mark.asyncio
async def test_create_po_inactive_supplier_raises_supplier_inactive(service):
    supplier = MagicMock(is_active=False)
    supplier.id = uuid4()
    service.supplier_repo.get_by_id.return_value = supplier

    with pytest.raises(SupplierInactiveException):
        await service.create_purchase_order(
            _create_payload(supplier.id), created_by=uuid4()
        )


@pytest.mark.asyncio
async def test_create_po_empty_lines_raises_validation_error(service):
    with pytest.raises(Exception):
        POCreate(supplier_id=uuid4(), lines=[])


@pytest.mark.asyncio
async def test_create_po_duplicate_product_in_lines_raises_conflict(service):
    pid = uuid4()
    payload = POCreate(
        supplier_id=uuid4(),
        lines=[
            POLineCreate(
                product_id=pid, quantity_ordered=Decimal("1"), unit_price=Decimal("5")
            ),
            POLineCreate(
                product_id=pid, quantity_ordered=Decimal("1"), unit_price=Decimal("5")
            ),
        ],
    )
    with pytest.raises(ConflictException):
        await service.create_purchase_order(payload, created_by=uuid4())


@pytest.mark.asyncio
async def test_submit_po_within_credit_limit_succeeds(service):
    po = DummyPO(status="draft")
    supplier = MagicMock(id=po.supplier_id, is_active=True, credit_limit=Decimal("100"))
    service.po_repo.get_by_id_for_update.return_value = po
    service.supplier_repo.get_by_id.return_value = supplier
    service.po_repo.get_open_exposure_for_supplier_for_update.return_value = Decimal(
        "50"
    )
    service.po_repo.get_by_id_with_lines.return_value = po

    result = await service.submit_purchase_order(po.id)
    assert result.status == "submitted"


@pytest.mark.asyncio
async def test_submit_po_exceeds_credit_limit_raises_with_gap(service):
    po = DummyPO(status="draft")
    po.total_amount = Decimal("80")
    supplier = MagicMock(id=po.supplier_id, is_active=True, credit_limit=Decimal("100"))
    service.po_repo.get_by_id_for_update.return_value = po
    service.supplier_repo.get_by_id.return_value = supplier
    service.po_repo.get_open_exposure_for_supplier_for_update.return_value = Decimal(
        "30"
    )

    with pytest.raises(CreditLimitExceededException) as exc:
        await service.submit_purchase_order(po.id)
    assert Decimal(exc.value.details["gap"]) == Decimal("10")


@pytest.mark.asyncio
async def test_submit_po_zero_credit_limit_always_fails(service):
    po = DummyPO(status="draft")
    po.total_amount = Decimal("1")
    supplier = MagicMock(id=po.supplier_id, is_active=True, credit_limit=Decimal("0"))
    service.po_repo.get_by_id_for_update.return_value = po
    service.supplier_repo.get_by_id.return_value = supplier
    service.po_repo.get_open_exposure_for_supplier_for_update.return_value = Decimal(
        "0"
    )

    with pytest.raises(CreditLimitExceededException):
        await service.submit_purchase_order(po.id)


@pytest.mark.asyncio
async def test_submit_po_excludes_received_closed_from_exposure(service):
    po = DummyPO(status="draft")
    supplier = MagicMock(id=po.supplier_id, is_active=True, credit_limit=Decimal("30"))
    service.po_repo.get_by_id_for_update.return_value = po
    service.supplier_repo.get_by_id.return_value = supplier
    service.po_repo.get_open_exposure_for_supplier_for_update.return_value = Decimal(
        "0"
    )
    service.po_repo.get_by_id_with_lines.return_value = po

    result = await service.submit_purchase_order(po.id)
    assert result.status == "submitted"


@pytest.mark.asyncio
async def test_cancel_po_from_draft_succeeds(service):
    po = DummyPO(status="draft")
    service.po_repo.get_by_id_for_update.return_value = po
    service.po_repo.get_by_id_with_lines.return_value = po

    result = await service.cancel_purchase_order(po.id)
    assert result.status == "cancelled"


@pytest.mark.asyncio
async def test_cancel_po_from_submitted_succeeds(service):
    po = DummyPO(status="submitted")
    service.po_repo.get_by_id_for_update.return_value = po
    service.po_repo.get_by_id_with_lines.return_value = po

    result = await service.cancel_purchase_order(po.id)
    assert result.status == "cancelled"


@pytest.mark.asyncio
async def test_cancel_po_from_acknowledged_raises_invalid_transition(service):
    po = DummyPO(status="acknowledged")
    service.po_repo.get_by_id_for_update.return_value = po

    with pytest.raises(InvalidStateTransitionException):
        await service.cancel_purchase_order(po.id)


@pytest.mark.asyncio
async def test_update_po_draft_succeeds(service):
    po = DummyPO(status="draft")
    service.po_repo.get_by_id_for_update.return_value = po
    service.po_repo.get_by_id_with_lines.return_value = po
    service.po_line_repo.list_by_po_id.return_value = po.lines

    update = POUpdate(
        notes="updated",
        lines=[
            POLineUpdate(
                product_id=uuid4(),
                quantity_ordered=Decimal("3"),
                unit_price=Decimal("10"),
            )
        ],
    )
    result = await service.update_purchase_order(po.id, update)
    assert result.status == "draft"


@pytest.mark.asyncio
async def test_update_po_non_draft_raises_invalid_transition(service):
    po = DummyPO(status="submitted")
    service.po_repo.get_by_id_for_update.return_value = po

    update = POUpdate(
        notes="updated",
        lines=[
            POLineUpdate(
                product_id=uuid4(),
                quantity_ordered=Decimal("3"),
                unit_price=Decimal("10"),
            )
        ],
    )
    with pytest.raises(InvalidStateTransitionException):
        await service.update_purchase_order(po.id, update)


@pytest.mark.asyncio
async def test_recalculate_total_sums_all_line_totals(service):
    po = DummyPO(status="draft")
    po.lines = [DummyLine(po.id), DummyLine(po.id)]
    po.lines[0].line_total = Decimal("10")
    po.lines[1].line_total = Decimal("25")

    service.po_line_repo.list_by_po_id.return_value = po.lines
    service.po_repo.get_by_id_for_update.return_value = po

    await service._recalculate_total(po.id)
    assert po.total_amount == Decimal("35")


@pytest.mark.asyncio
async def test_list_purchase_orders_staff_sees_only_own(service):
    params = POListParams()
    await service.list_purchase_orders(params, uuid4(), UserRole.WAREHOUSE_STAFF)
    service.po_repo.list_with_filters.assert_called_once()
