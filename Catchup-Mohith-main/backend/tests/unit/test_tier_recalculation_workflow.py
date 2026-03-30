# backend/tests/unit/test_tier_recalculation_workflow.py
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.app.temporal.activities import tier_activities
from backend.app.temporal.workflows.tier_recalculation import TierRecalculationWorkflow

pytestmark = pytest.mark.asyncio


class _FakeResult:
    def __init__(self, scalar=None, scalars=None):
        self._scalar = scalar
        self._scalars = scalars or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalar_one(self):
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


def _patch_session_factory(monkeypatch, session):
    monkeypatch.setattr(
        tier_activities,
        "AsyncSessionLocal",
        lambda: _SessionFactory(session),
    )


def _decision(new_tier="Gold", reason="ok", on_time=2, late=0):
    return SimpleNamespace(
        new_tier=new_tier,
        decision_reason=reason,
        consecutive_qualifying_months=on_time,
        consecutive_underperforming_months=late,
    )


async def test_calculate_supplier_tier_calls_compute_tier_decision(monkeypatch):
    supplier = SimpleNamespace(
        id=uuid4(),
        current_tier="Silver",
        tier_locked=False,
        consecutive_on_time=0,
        consecutive_late=0,
        deleted_at=None,
    )
    session = _FakeSession(
        [
            _FakeResult(scalar=supplier),
            _FakeResult(scalar=25),
            _FakeResult(scalar=2),
            _FakeResult(scalar=None),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    spy = AsyncMock(return_value=None)
    monkeypatch.setattr(tier_activities, "_upsert_metrics_history", spy)
    compute = MagicMock(return_value=_decision())
    monkeypatch.setattr(tier_activities, "compute_tier_decision", compute)
    await tier_activities.calculate_supplier_tier(str(supplier.id), 2026, 3)
    compute.assert_called_once()


async def test_calculate_supplier_tier_writes_metrics_history(monkeypatch):
    supplier = SimpleNamespace(
        id=uuid4(),
        current_tier="Silver",
        tier_locked=False,
        consecutive_on_time=0,
        consecutive_late=0,
        deleted_at=None,
    )
    session = _FakeSession(
        [
            _FakeResult(scalar=supplier),
            _FakeResult(scalar=30),
            _FakeResult(scalar=3),
            _FakeResult(scalar=None),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    upsert = AsyncMock(return_value=None)
    monkeypatch.setattr(tier_activities, "_upsert_metrics_history", upsert)
    monkeypatch.setattr(
        tier_activities,
        "compute_tier_decision",
        lambda *_: _decision(),
    )
    await tier_activities.calculate_supplier_tier(str(supplier.id), 2026, 3)
    upsert.assert_awaited_once()


async def test_calculate_supplier_tier_updates_supplier_fields(monkeypatch):
    supplier = SimpleNamespace(
        id=uuid4(),
        current_tier="Silver",
        tier_locked=False,
        consecutive_on_time=1,
        consecutive_late=2,
        deleted_at=None,
    )
    session = _FakeSession(
        [
            _FakeResult(scalar=supplier),
            _FakeResult(scalar=40),
            _FakeResult(scalar=1),
            _FakeResult(scalar=None),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    monkeypatch.setattr(tier_activities, "_upsert_metrics_history", AsyncMock())
    monkeypatch.setattr(
        tier_activities,
        "compute_tier_decision",
        lambda *_: _decision(new_tier="Gold", on_time=5, late=0),
    )
    await tier_activities.calculate_supplier_tier(str(supplier.id), 2026, 3)
    assert supplier.current_tier == "Gold"
    assert supplier.consecutive_on_time == 5
    assert supplier.consecutive_late == 0


async def test_calculate_supplier_tier_insufficient_data_preserved(monkeypatch):
    supplier = SimpleNamespace(
        id=uuid4(),
        current_tier="Silver",
        tier_locked=False,
        consecutive_on_time=0,
        consecutive_late=0,
        deleted_at=None,
    )
    session = _FakeSession(
        [
            _FakeResult(scalar=supplier),
            _FakeResult(scalar=10),
            _FakeResult(scalar=1),
            _FakeResult(scalar=None),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    upsert = AsyncMock()
    monkeypatch.setattr(tier_activities, "_upsert_metrics_history", upsert)
    result = await tier_activities.calculate_supplier_tier(str(supplier.id), 2026, 3)
    assert result["insufficient_data"] is True
    assert result["new_tier"] == "Silver"
    _, kwargs = upsert.await_args
    assert kwargs["insufficient_data"] is True


async def test_calculate_supplier_tier_returns_unchanged_tier(monkeypatch):
    supplier = SimpleNamespace(
        id=uuid4(),
        current_tier="Silver",
        tier_locked=False,
        consecutive_on_time=0,
        consecutive_late=0,
        deleted_at=None,
    )
    session = _FakeSession(
        [
            _FakeResult(scalar=supplier),
            _FakeResult(scalar=25),
            _FakeResult(scalar=1),
            _FakeResult(scalar=None),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    monkeypatch.setattr(tier_activities, "_upsert_metrics_history", AsyncMock())
    monkeypatch.setattr(
        tier_activities,
        "compute_tier_decision",
        lambda *_: _decision(new_tier="Silver"),
    )
    result = await tier_activities.calculate_supplier_tier(str(supplier.id), 2026, 3)
    assert result["old_tier"] == result["new_tier"]
    assert result["tier_changed"] is False


async def test_calculate_supplier_tier_returns_changed_tier(monkeypatch):
    supplier = SimpleNamespace(
        id=uuid4(),
        current_tier="Silver",
        tier_locked=False,
        consecutive_on_time=0,
        consecutive_late=0,
        deleted_at=None,
    )
    session = _FakeSession(
        [
            _FakeResult(scalar=supplier),
            _FakeResult(scalar=25),
            _FakeResult(scalar=1),
            _FakeResult(scalar=None),
        ]
    )
    _patch_session_factory(monkeypatch, session)
    monkeypatch.setattr(tier_activities, "_upsert_metrics_history", AsyncMock())
    monkeypatch.setattr(
        tier_activities,
        "compute_tier_decision",
        lambda *_: _decision(new_tier="Gold"),
    )
    result = await tier_activities.calculate_supplier_tier(str(supplier.id), 2026, 3)
    assert result["old_tier"] != result["new_tier"]
    assert result["tier_changed"] is True


async def test_tier_recalculation_workflow_sends_email_on_tier_change(monkeypatch):
    workflow = TierRecalculationWorkflow()
    calls = []

    async def _fake_execute_activity(fn, *args, **kwargs):
        calls.append(getattr(fn, "__name__", str(fn)))
        if calls[-1] == "get_all_active_suppliers":
            return ["sup-1"]
        if calls[-1] == "calculate_supplier_tier":
            return {
                "insufficient_data": False,
                "old_tier": "Silver",
                "new_tier": "Gold",
                "tier_changed": True,
            }
        return None

    monkeypatch.setattr(
        "backend.app.temporal.workflows.tier_recalculation.workflow.execute_activity",
        _fake_execute_activity,
    )
    await workflow.run(2026, 3)
    assert "send_tier_change_email" in calls


async def test_monthly_summary_sent_after_all_suppliers_processed(monkeypatch):
    workflow = TierRecalculationWorkflow()
    calls = []

    async def _fake_execute_activity(fn, *args, **kwargs):
        calls.append(getattr(fn, "__name__", str(fn)))
        if len(calls) == 1:
            return ["sup-1", "sup-2"]
        if "calculate_supplier_tier" in calls[-1]:
            return {
                "insufficient_data": False,
                "old_tier": "Silver",
                "new_tier": "Gold",
                "tier_changed": True,
            }
        return None

    monkeypatch.setattr(
        "backend.app.temporal.workflows.tier_recalculation.workflow.execute_activity",
        _fake_execute_activity,
    )
    await workflow.run(2026, 3)
    assert calls[0] == "get_all_active_suppliers"
    assert calls[-1] == "send_monthly_summary_email"
