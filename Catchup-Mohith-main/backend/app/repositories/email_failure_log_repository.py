# backend/app/repositories/email_failure_log_repository.py
import logging
from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.email_failure_log import EmailFailureLog
from backend.app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class EmailFailureLogRepository(BaseRepository[EmailFailureLog]):
    """
    Persistence layer for email_failure_log records.

    All write methods are designed to be safe to call in an
    except block — they do not re-raise on their own failures so
    that email logging never causes secondary exceptions in
    activities.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(EmailFailureLog, session)

    async def log_failure(
        self,
        *,
        email_type: str,
        to_emails: list[str],
        subject: str,
        body: str,
        error_message: str,
        workflow_id: str | None = None,
        activity_id: str | None = None,
    ) -> EmailFailureLog:
        """
        Insert a new failure record with retry_count=0 and resolved=False.

        Returns the persisted record. The caller should already be
        inside a database transaction (activity session).
        """
        record = EmailFailureLog(
            email_type=email_type,
            to_emails=to_emails,
            subject=subject,
            body=body,
            error_message=error_message,
            retry_count=0,
            resolved=False,
            workflow_id=workflow_id,
            activity_id=activity_id,
        )
        return await self.create(record)

    async def increment_retry(self, record_id: UUID) -> EmailFailureLog | None:
        """
        Increment retry_count by 1 and persist.

        Returns None if the record is not found.
        """
        record = await self.get_by_id(record_id)
        if record is None:
            logger.warning(
                "EmailFailureLog record %s not found for retry increment", record_id
            )
            return None
        record.retry_count += 1
        record.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def mark_resolved(self, record_id: UUID) -> EmailFailureLog | None:
        """
        Set resolved=True on the given record.

        Returns None if the record is not found.
        """
        record = await self.get_by_id(record_id)
        if record is None:
            logger.warning("EmailFailureLog record %s not found for resolve", record_id)
            return None
        record.resolved = True
        record.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def get_unresolved(
        self,
        limit: int = 100,
    ) -> Sequence[EmailFailureLog]:
        """
        Return up to `limit` unresolved failure records ordered by
        created_at ascending (oldest first).
        """
        result = await self.session.execute(
            select(EmailFailureLog)
            .where(EmailFailureLog.resolved.is_(False))
            .order_by(EmailFailureLog.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
