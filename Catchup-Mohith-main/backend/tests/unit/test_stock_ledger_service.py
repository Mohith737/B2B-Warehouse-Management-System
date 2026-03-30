# /home/mohith/Catchup-Mohith/backend/tests/unit/test_stock_ledger_service.py
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.app.core.exceptions import (
    InvalidCursorException,
    InsufficientStockException,
)
from backend.app.services.stock_ledger_service import StockLedgerService


def _mock_session() -> MagicMock:
    session = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_add_entry_increases_current_stock(monkeypatch):
    service = StockLedgerService()
    session = _mock_session()
    product_id = uuid4()

    product = SimpleNamespace(id=product_id, current_stock=Decimal("5.0000"))
    product_repo = MagicMock()
    product_repo.get_by_id_for_update = AsyncMock(return_value=product)

    now = datetime.now(timezone.utc)
    created_entry = SimpleNamespace(
        id=uuid4(),
        product_id=product_id,
        quantity_change=Decimal("3.0000"),
        change_type="grn_receipt",
        reference_id=None,
        notes=None,
        balance_after=Decimal("8.0000"),
        created_at=now,
    )
    ledger_repo = MagicMock()
    ledger_repo.create = AsyncMock(return_value=created_entry)

    monkeypatch.setattr(
        "backend.app.services.stock_ledger_service.ProductRepository",
        lambda _: product_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.stock_ledger_service.StockLedgerRepository",
        lambda _: ledger_repo,
    )

    result = await service.add_entry(
        session=session,
        product_id=product_id,
        quantity_change=Decimal("3.0000"),
        change_type="grn_receipt",
        reference_id=None,
        notes="receipt",
    )

    assert result.balance_after == Decimal("8.0000")
    assert product.current_stock == Decimal("8.0000")
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_entry_would_make_stock_negative_raises_insufficient(monkeypatch):
    service = StockLedgerService()
    session = _mock_session()
    product_id = uuid4()

    product = SimpleNamespace(id=product_id, current_stock=Decimal("1.0000"))
    product_repo = MagicMock()
    product_repo.get_by_id_for_update = AsyncMock(return_value=product)
    ledger_repo = MagicMock()
    ledger_repo.create = AsyncMock()

    monkeypatch.setattr(
        "backend.app.services.stock_ledger_service.ProductRepository",
        lambda _: product_repo,
    )
    monkeypatch.setattr(
        "backend.app.services.stock_ledger_service.StockLedgerRepository",
        lambda _: ledger_repo,
    )

    with pytest.raises(InsufficientStockException):
        await service.add_entry(
            session=session,
            product_id=product_id,
            quantity_change=Decimal("-2.0000"),
            change_type="po_reservation",
            reference_id=None,
            notes="reserve",
        )

    ledger_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_page_invalid_cursor_raises_invalid_cursor(monkeypatch):
    service = StockLedgerService()
    session = _mock_session()
    ledger_repo = MagicMock()
    ledger_repo.get_page_with_cursor = AsyncMock()
    monkeypatch.setattr(
        "backend.app.services.stock_ledger_service.StockLedgerRepository",
        lambda _: ledger_repo,
    )

    with pytest.raises(InvalidCursorException):
        await service.get_page(session=session, cursor="not-a-uuid")


@pytest.mark.asyncio
async def test_get_page_returns_cursor_meta_when_more_exist(monkeypatch):
    service = StockLedgerService()
    session = _mock_session()
    product_id = uuid4()
    cursor_id = uuid4()

    now = datetime.now(timezone.utc)
    first = SimpleNamespace(
        id=uuid4(),
        product_id=product_id,
        quantity_change=Decimal("1.0000"),
        change_type="grn_receipt",
        reference_id=None,
        notes=None,
        balance_after=Decimal("1.0000"),
        created_at=now,
    )
    second = SimpleNamespace(
        id=uuid4(),
        product_id=product_id,
        quantity_change=Decimal("2.0000"),
        change_type="grn_receipt",
        reference_id=None,
        notes=None,
        balance_after=Decimal("3.0000"),
        created_at=now,
    )

    ledger_repo = MagicMock()
    ledger_repo.get_page_with_cursor = AsyncMock(
        return_value=([first, second], cursor_id)
    )
    monkeypatch.setattr(
        "backend.app.services.stock_ledger_service.StockLedgerRepository",
        lambda _: ledger_repo,
    )

    items, next_cursor = await service.get_page(session=session, limit=2)
    assert len(items) == 2
    assert next_cursor == cursor_id
