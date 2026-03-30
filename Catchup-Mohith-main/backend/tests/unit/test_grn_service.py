# /home/mohith/Catchup-Mohith/backend/tests/unit/test_grn_service.py
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.app.core.exceptions import (
    BarcodeMismatchException,
    InvalidStateTransitionException,
    NotFoundException,
    OverReceiptException,
)
from backend.app.models.grn import GRNStatus
from backend.app.models.purchase_order import POStatus
from backend.app.schemas.grn import GRNLineCreate
from backend.app.services.grn_service import GRNService


def _async_cm() -> MagicMock:
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=None)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _mock_session() -> MagicMock:
    session = MagicMock()
    session.begin = MagicMock(return_value=_async_cm())
    session.flush = AsyncMock()
    return session


def _make_grn(
    po_id=None,
    status: str = GRNStatus.OPEN.value,
):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        po_id=po_id or uuid4(),
        status=status,
        completed_at=None,
        auto_reorder_triggered=False,
        created_by=uuid4(),
        created_at=now,
        updated_at=now,
        lines=[],
    )


def _make_grn_line(grn_id, product_id, qty: str = "3.0000"):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        grn_id=grn_id,
        product_id=product_id,
        quantity_received=Decimal(qty),
        unit_cost=Decimal("10.0000"),
        barcode_scanned=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_create_grn_against_non_shipped_raises_invalid_transition(monkeypatch):
    session = _mock_session()
    service = GRNService()
    po_id = uuid4()
    user_id = uuid4()

    po_repo = MagicMock()
    po_repo.get_by_id_for_update = AsyncMock(
        return_value=SimpleNamespace(id=po_id, status=POStatus.DRAFT.value)
    )
    grn_repo = MagicMock()

    monkeypatch.setattr(
        "backend.app.services.grn_service.PurchaseOrderRepository", lambda _: po_repo
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.GRNRepository", lambda _: grn_repo
    )

    with pytest.raises(InvalidStateTransitionException):
        await service.create_grn(po_id=po_id, created_by=user_id, session=session)


@pytest.mark.asyncio
async def test_add_line_over_receipt_raises_over_receipt(monkeypatch):
    session = _mock_session()
    service = GRNService()
    po_id = uuid4()
    product_id = uuid4()
    grn = _make_grn(po_id=po_id, status=GRNStatus.OPEN.value)

    grn_repo = MagicMock()
    grn_repo.get_by_id_with_lines = AsyncMock(return_value=grn)

    grn_line_repo = MagicMock()
    grn_line_repo.get_by_grn_and_product = AsyncMock(return_value=None)
    grn_line_repo.get_total_received_for_po_line = AsyncMock(
        return_value=Decimal("4.0000")
    )

    po_line = SimpleNamespace(
        id=uuid4(),
        product_id=product_id,
        quantity_ordered=Decimal("5.0000"),
    )
    po_line_repo = MagicMock()
    po_line_repo.get_by_po_id_product_id = AsyncMock(return_value=po_line)

    product_repo = MagicMock()

    monkeypatch.setattr(
        "backend.app.services.grn_service.GRNRepository", lambda _: grn_repo
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.GRNLineRepository",
        lambda _: grn_line_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.POLineRepository",
        lambda _: po_line_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.ProductRepository",
        lambda _: product_repo,
    )

    payload = GRNLineCreate(
        product_id=product_id,
        quantity_received=Decimal("2.0000"),
        unit_cost=Decimal("10.0000"),
        barcode_scanned=None,
    )

    with pytest.raises(OverReceiptException):
        await service.add_line(grn_id=grn.id, data=payload, session=session)


@pytest.mark.asyncio
async def test_add_line_barcode_mismatch_raises_barcode_mismatch(monkeypatch):
    session = _mock_session()
    service = GRNService()
    po_id = uuid4()
    expected_product_id = uuid4()
    scanned_product_id = uuid4()
    grn = _make_grn(po_id=po_id, status=GRNStatus.OPEN.value)

    grn_repo = MagicMock()
    grn_repo.get_by_id_with_lines = AsyncMock(return_value=grn)

    grn_line_repo = MagicMock()
    grn_line_repo.get_by_grn_and_product = AsyncMock(return_value=None)
    grn_line_repo.get_total_received_for_po_line = AsyncMock(return_value=Decimal("0"))

    po_line = SimpleNamespace(
        id=uuid4(),
        product_id=expected_product_id,
        quantity_ordered=Decimal("10.0000"),
    )
    po_line_repo = MagicMock()
    po_line_repo.get_by_po_id_product_id = AsyncMock(return_value=po_line)

    product_repo = MagicMock()
    product_repo.get_by_barcode = AsyncMock(
        return_value=SimpleNamespace(id=scanned_product_id)
    )

    monkeypatch.setattr(
        "backend.app.services.grn_service.GRNRepository", lambda _: grn_repo
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.GRNLineRepository",
        lambda _: grn_line_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.POLineRepository",
        lambda _: po_line_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.ProductRepository",
        lambda _: product_repo,
    )

    payload = GRNLineCreate(
        product_id=expected_product_id,
        quantity_received=Decimal("1.0000"),
        unit_cost=Decimal("10.0000"),
        barcode_scanned="BC-123",
    )

    with pytest.raises(BarcodeMismatchException):
        await service.add_line(grn_id=grn.id, data=payload, session=session)


@pytest.mark.asyncio
async def test_complete_grn_partial_creates_backorder(monkeypatch):
    session = _mock_session()
    service = GRNService()
    product_id = uuid4()
    grn = _make_grn(status=GRNStatus.OPEN.value)
    line = _make_grn_line(grn.id, product_id, qty="4.0000")

    grn_repo = MagicMock()
    grn_repo.get_by_id_with_lines = AsyncMock(side_effect=[grn, grn])

    grn_line_repo = MagicMock()
    grn_line_repo.get_lines_for_grn = AsyncMock(return_value=[line])
    grn_line_repo.get_total_received_for_po_line = AsyncMock(
        return_value=Decimal("4.0000")
    )

    po = SimpleNamespace(id=grn.po_id, status=POStatus.SHIPPED.value, received_at=None)
    po_repo = MagicMock()
    po_repo.get_by_id_for_update = AsyncMock(return_value=po)

    po_line = SimpleNamespace(
        id=uuid4(),
        product_id=product_id,
        quantity_ordered=Decimal("10.0000"),
    )
    po_line_repo = MagicMock()
    po_line_repo.list_by_po_id = AsyncMock(return_value=[po_line])

    product_repo = MagicMock()
    product_repo.get_by_id = AsyncMock(
        return_value=SimpleNamespace(
            id=product_id,
            current_stock=Decimal("4.0000"),
            reorder_point=Decimal("5.0000"),
            low_stock_threshold_override=None,
        )
    )

    backorder_repo = MagicMock()
    backorder_repo.create_backorder = AsyncMock()

    service.stock_ledger_service.add_entry = AsyncMock()

    monkeypatch.setattr(
        "backend.app.services.grn_service.GRNRepository", lambda _: grn_repo
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.GRNLineRepository",
        lambda _: grn_line_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.PurchaseOrderRepository",
        lambda _: po_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.POLineRepository",
        lambda _: po_line_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.ProductRepository",
        lambda _: product_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.grn_service.BackorderRepository",
        lambda _: backorder_repo,
    )

    result = await service.complete_grn(grn_id=grn.id, session=session)

    assert result.status == GRNStatus.COMPLETED.value
    assert result.auto_reorder_triggered is True
    backorder_repo.create_backorder.assert_awaited_once()
    service.stock_ledger_service.add_entry.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_grn_not_found_raises_not_found(monkeypatch):
    session = _mock_session()
    service = GRNService()
    grn_repo = MagicMock()
    grn_repo.get_by_id_with_lines = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "backend.app.services.grn_service.GRNRepository", lambda _: grn_repo
    )

    with pytest.raises(NotFoundException):
        await service.get_grn(grn_id=uuid4(), session=session)
