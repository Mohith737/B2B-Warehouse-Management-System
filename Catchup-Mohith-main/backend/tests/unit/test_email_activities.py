# backend/tests/unit/test_email_activities.py
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.temporal.activities import email_activities

pytestmark = pytest.mark.asyncio


class _SessionFactory:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _AsyncCtx:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def begin(self):
        return _AsyncCtx()


async def test_send_email_uses_sandbox_in_non_production(monkeypatch):
    send_fn = MagicMock()
    service = MagicMock(send=send_fn)
    monkeypatch.setattr(email_activities, "EmailService", lambda: service)
    result = await email_activities.send_email(
        to_emails=["x@test.com"],
        subject="s",
        body="b",
        email_type="monthly_summary",
        workflow_id="wf",
        activity_id="act",
    )
    assert result["success"] is True
    send_fn.assert_called_once()


async def test_send_email_uses_real_sendgrid_in_production(monkeypatch):
    send_fn = MagicMock()
    service = MagicMock(send=send_fn)
    monkeypatch.setattr(email_activities, "EmailService", lambda: service)
    result = await email_activities.send_email(
        to_emails=["x@test.com"],
        subject="s",
        body="b",
        email_type="monthly_summary",
        workflow_id="wf",
        activity_id="act",
    )
    assert result["success"] is True
    send_fn.assert_called_once()


async def test_send_email_failure_logs_to_email_failure_log(monkeypatch):
    monkeypatch.setattr(
        email_activities,
        "EmailService",
        lambda: MagicMock(send=MagicMock(side_effect=RuntimeError("sendgrid down"))),
    )
    repo = MagicMock()
    repo.log_failure = AsyncMock()
    monkeypatch.setattr(email_activities, "EmailFailureLogRepository", lambda _s: repo)
    monkeypatch.setattr(
        email_activities,
        "AsyncSessionLocal",
        lambda: _SessionFactory(_FakeSession()),
    )
    result = await email_activities.send_email(
        to_emails=["x@test.com"],
        subject="s",
        body="b",
        email_type="monthly_summary",
        workflow_id="wf-1",
        activity_id="act-1",
    )
    assert result["success"] is False
    repo.log_failure.assert_awaited_once()
    _, kwargs = repo.log_failure.await_args
    assert kwargs["workflow_id"] == "wf-1"
    assert kwargs["activity_id"] == "act-1"
    assert kwargs["email_type"] == "monthly_summary"


async def test_send_email_failure_does_not_raise(monkeypatch):
    monkeypatch.setattr(
        email_activities,
        "EmailService",
        lambda: MagicMock(send=MagicMock(side_effect=RuntimeError("boom"))),
    )
    repo = MagicMock()
    repo.log_failure = AsyncMock()
    monkeypatch.setattr(email_activities, "EmailFailureLogRepository", lambda _s: repo)
    monkeypatch.setattr(
        email_activities,
        "AsyncSessionLocal",
        lambda: _SessionFactory(_FakeSession()),
    )
    result = await email_activities.send_email(
        to_emails=["x@test.com"],
        subject="s",
        body="b",
        email_type="backorder_notification",
        workflow_id="wf",
        activity_id="act",
    )
    assert result["success"] is False
    assert "error" in result


async def test_send_email_failure_sets_retry_count(monkeypatch):
    monkeypatch.setattr(
        email_activities,
        "EmailService",
        lambda: MagicMock(send=MagicMock(side_effect=RuntimeError("boom"))),
    )
    captured = {}

    class _Repo:
        async def log_failure(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(retry_count=0, resolved=False)

    monkeypatch.setattr(
        email_activities,
        "EmailFailureLogRepository",
        lambda _s: _Repo(),
    )
    monkeypatch.setattr(
        email_activities,
        "AsyncSessionLocal",
        lambda: _SessionFactory(_FakeSession()),
    )
    await email_activities.send_email(
        to_emails=["x@test.com"],
        subject="s",
        body="b",
        email_type="monthly_summary",
        workflow_id="wf",
        activity_id="act",
    )
    assert captured["email_type"] == "monthly_summary"


async def test_email_failure_log_resolved_flag_defaults_false(monkeypatch):
    monkeypatch.setattr(
        email_activities,
        "EmailService",
        lambda: MagicMock(send=MagicMock(side_effect=RuntimeError("boom"))),
    )

    class _Repo:
        async def log_failure(self, **kwargs):
            return SimpleNamespace(resolved=False, retry_count=0, **kwargs)

    monkeypatch.setattr(
        email_activities,
        "EmailFailureLogRepository",
        lambda _s: _Repo(),
    )
    monkeypatch.setattr(
        email_activities,
        "AsyncSessionLocal",
        lambda: _SessionFactory(_FakeSession()),
    )
    result = await email_activities.send_email(
        to_emails=["x@test.com"],
        subject="s",
        body="b",
        email_type="monthly_summary",
        workflow_id="wf",
        activity_id="act",
    )
    assert result["success"] is False
