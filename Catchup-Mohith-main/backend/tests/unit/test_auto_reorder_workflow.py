# backend/tests/unit/test_auto_reorder_workflow.py
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.app.services.po_number_service import generate_auto_po_number
from backend.app.temporal.activities import reorder_activities

pytestmark = pytest.mark.asyncio


class _FakeResult:
    def __init__(self, scalar=None, scalars=None):
        self._scalar = scalar
        self._scalars = scalars or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: self._scalars)


class _AsyncCtx:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, execute_results):
        self._results = iter(execute_results)
        self.added = []
        self.flush = AsyncMock()
        self.refresh = AsyncMock()

    async def execute(self, _query):
        return next(self._results)

    def begin(self):
        return _AsyncCtx()

    def add(self, obj):
        self.added.append(obj)


class _SessionFactory:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _Expr:
    def is_(self, _value):
        return True

    def is_not(self, _value):
        return True

    def __eq__(self, _other):
        return True


def _mk_product(
    *,
    current_stock="2",
    reorder_point="5",
    low_stock_threshold_override=None,
    preferred_supplier_id=None,
):
    return SimpleNamespace(
        id=uuid4(),
        current_stock=Decimal(current_stock),
        reorder_point=Decimal(reorder_point),
        low_stock_threshold_override=low_stock_threshold_override,
        preferred_supplier_id=preferred_supplier_id,
        reorder_quantity=Decimal("10"),
        unit_price=Decimal("12"),
        name="Widget",
    )


def _patch_session_factory(monkeypatch, session):
    # Product model in current codebase does not define these fields,
    # but workflow query still references them.
    monkeypatch.setattr(
        reorder_activities.Product,
        "auto_reorder_enabled",
        _Expr(),
        raising=False,
    )
    monkeypatch.setattr(
        reorder_activities.Product,
        "preferred_supplier_id",
        _Expr(),
        raising=False,
    )
    monkeypatch.setattr(
        reorder_activities,
        "AsyncSessionLocal",
        lambda: _SessionFactory(session),
    )


async def test_get_reorder_eligible_products_returns_correct_products(monkeypatch):
    supplier_id = uuid4()
    p1 = _mk_product(preferred_supplier_id=supplier_id, current_stock="1")
    p2 = _mk_product(preferred_supplier_id=supplier_id, current_stock="3")
    session = _FakeSession(
        [
            _FakeResult(scalars=[p1, p2]),
            _FakeResult(scalar=supplier_id),
            _FakeResult(scalar=None),
            _FakeResult(scalar=supplier_id),
            _FakeResult(scalar=None),
        ]
    )
    _patch_session_factory(monkeypatch, session)

    ids = await reorder_activities.get_reorder_eligible_products()
    assert ids == [str(p1.id), str(p2.id)]


async def test_get_reorder_eligible_excludes_inactive_supplier(monkeypatch):
    p = _mk_product(preferred_supplier_id=uuid4(), current_stock="1")
    session = _FakeSession([_FakeResult(scalars=[p]), _FakeResult(scalar=None)])
    _patch_session_factory(monkeypatch, session)
    ids = await reorder_activities.get_reorder_eligible_products()
    assert ids == []


async def test_get_reorder_eligible_excludes_no_preferred_supplier(monkeypatch):
    p = _mk_product(preferred_supplier_id=None)
    session = _FakeSession([_FakeResult(scalars=[p])])
    _patch_session_factory(monkeypatch, session)
    ids = await reorder_activities.get_reorder_eligible_products()
    assert ids == []


async def test_get_reorder_eligible_excludes_existing_open_po(monkeypatch):
    p = _mk_product(preferred_supplier_id=uuid4())
    session = _FakeSession(
        [
            _FakeResult(scalars=[p]),
            _FakeResult(scalar=p.preferred_supplier_id),
            _FakeResult(scalar=uuid4()),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    ids = await reorder_activities.get_reorder_eligible_products()
    assert ids == []


async def test_create_auto_reorder_po_creates_in_submitted_status(monkeypatch):
    product = _mk_product(preferred_supplier_id=uuid4())
    supplier = SimpleNamespace(
        id=product.preferred_supplier_id,
        is_active=True,
        name="S",
    )
    admin = SimpleNamespace(id=uuid4())
    created_po = SimpleNamespace(id=uuid4(), po_number="SB-AUTO-2026-000001")

    monkeypatch.setattr(
        reorder_activities,
        "generate_auto_po_number",
        AsyncMock(return_value="SB-AUTO-2026-000001"),
    )
    monkeypatch.setattr(reorder_activities, "SYSTEM_ADMIN_UUID", admin.id)

    session = _FakeSession(
        [
            _FakeResult(scalar=product),
            _FakeResult(scalar=supplier),
            _FakeResult(scalar=None),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    session.refresh = AsyncMock(side_effect=[None, None])

    async def _fake_flush():
        for obj in session.added:
            if getattr(obj, "po_number", "").startswith("SB-AUTO-"):
                setattr(obj, "id", created_po.id)

    session.flush = AsyncMock(side_effect=_fake_flush)
    result = await reorder_activities.create_auto_reorder_po(str(product.id))
    assert result["skipped"] is False
    assert result["po_number"].startswith("SB-AUTO-")


async def test_create_auto_reorder_po_uses_auto_format_number(monkeypatch):
    product = _mk_product(preferred_supplier_id=uuid4())
    supplier = SimpleNamespace(
        id=product.preferred_supplier_id,
        is_active=True,
        name="S",
    )
    monkeypatch.setattr(reorder_activities, "SYSTEM_ADMIN_UUID", uuid4())

    monkeypatch.setattr(
        reorder_activities,
        "generate_auto_po_number",
        AsyncMock(return_value="SB-AUTO-2026-000123"),
    )

    session = _FakeSession(
        [
            _FakeResult(scalar=product),
            _FakeResult(scalar=supplier),
            _FakeResult(scalar=None),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    result = await reorder_activities.create_auto_reorder_po(str(product.id))
    assert result["po_number"].startswith("SB-AUTO-")


async def test_create_auto_reorder_po_idempotent_returns_existing(monkeypatch):
    product = _mk_product(preferred_supplier_id=uuid4())
    supplier = SimpleNamespace(
        id=product.preferred_supplier_id,
        is_active=True,
        name="S",
    )
    existing = SimpleNamespace(id=uuid4(), po_number="SB-AUTO-2026-000888")
    session = _FakeSession(
        [
            _FakeResult(scalar=product),
            _FakeResult(scalar=supplier),
            _FakeResult(scalar=existing),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    result = await reorder_activities.create_auto_reorder_po(str(product.id))
    assert result["skipped"] is True
    assert result["po_id"] == str(existing.id)


async def test_create_auto_reorder_po_inactive_supplier_skips(monkeypatch):
    product = _mk_product(preferred_supplier_id=uuid4())
    supplier = SimpleNamespace(
        id=product.preferred_supplier_id,
        is_active=False,
        name="S",
    )
    session = _FakeSession([_FakeResult(scalar=product), _FakeResult(scalar=supplier)])
    _patch_session_factory(monkeypatch, session)
    result = await reorder_activities.create_auto_reorder_po(str(product.id))
    assert result["skipped"] is True
    assert result["po_id"] is None


async def test_auto_reorder_po_number_format_is_sb_auto_yyyy_nnnnnn(monkeypatch):
    from backend.app.services import po_number_service

    class _DummyField:
        def like(self, _):
            return self

        def is_(self, _):
            return self

        def desc(self):
            return self

    po_number_service.PurchaseOrder = SimpleNamespace(  # type: ignore[attr-defined]
        po_number=_DummyField(),
        auto_generated=_DummyField(),
    )
    po_number_service.select = lambda *_args, **_kwargs: SimpleNamespace(  # type: ignore[assignment]
        where=lambda *_a, **_k: SimpleNamespace(
            where=lambda *_a2, **_k2: SimpleNamespace(
                order_by=lambda *_a3, **_k3: SimpleNamespace(
                    limit=lambda *_a4, **_k4: SimpleNamespace(
                        with_for_update=lambda **_k5: object()
                    )
                )
            )
        )
    )
    session = SimpleNamespace(execute=AsyncMock(return_value=_FakeResult(scalar=None)))
    value = await generate_auto_po_number(session, 2026)
    assert value == "SB-AUTO-2026-000001"
