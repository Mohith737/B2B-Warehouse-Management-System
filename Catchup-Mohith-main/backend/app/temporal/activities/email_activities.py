# backend/app/temporal/activities/email_activities.py
import logging

from temporalio import activity

from backend.app.db.session import AsyncSessionLocal
from backend.app.repositories.email_failure_log_repository import (
    EmailFailureLogRepository,
)
from backend.app.services.email_service import EmailService

logger = logging.getLogger(__name__)


@activity.defn
async def send_email(
    to_emails: list[str],
    subject: str,
    body: str,
    email_type: str,
    workflow_id: str,
    activity_id: str,
) -> dict:
    """
    Send a single email via SendGrid.

    This activity NEVER raises. Any failure is caught, written to
    email_failure_log, and logged at ERROR level. The workflow
    continues regardless of email outcome.

    Returns:
        {"success": True} on successful send.
        {"success": False, "error": "<message>"} on any failure.
    """
    email_service = EmailService()
    try:
        email_service.send(
            to_emails=to_emails,
            subject=subject,
            body=body,
            email_type=email_type,
        )
        logger.info(
            "Email sent successfully email_type=%s workflow_id=%s to=%s",
            email_type,
            workflow_id,
            to_emails,
        )
        return {"success": True}
    except Exception as exc:
        error_message = str(exc)
        logger.error(
            "Email send failed email_type=%s workflow_id=%s to=%s error=%s",
            email_type,
            workflow_id,
            to_emails,
            error_message,
            exc_info=True,
        )
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    repo = EmailFailureLogRepository(session)
                    await repo.log_failure(
                        email_type=email_type,
                        to_emails=to_emails,
                        subject=subject,
                        body=body,
                        error_message=error_message,
                        workflow_id=workflow_id,
                        activity_id=activity_id,
                    )
        except Exception as log_exc:
            logger.error(
                "Failed to write email_failure_log email_type=%s error=%s",
                email_type,
                log_exc,
                exc_info=True,
            )
        return {"success": False, "error": error_message}
