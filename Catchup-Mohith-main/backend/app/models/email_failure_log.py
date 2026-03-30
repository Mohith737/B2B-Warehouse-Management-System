# backend/app/models/email_failure_log.py
from typing import Any

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EmailFailureLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Persists details of every failed email send attempt.

    Email failures must never fail a workflow — instead the
    context is written here so ops can retry or investigate.
    """

    __tablename__ = "email_failure_log"

    email_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    to_emails: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    workflow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<EmailFailureLog id={self.id} "
            f"email_type={self.email_type} resolved={self.resolved}>"
        )
