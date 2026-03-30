# backend/app/services/email_service.py
import logging
from typing import Sequence

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, MailSettings, SandBoxMode

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Thin wrapper around the SendGrid Python SDK.

    This service is only called from email_activities.py — never
    from business services directly.

    SendGrid sandbox mode is enabled in all non-production
    environments so emails appear in SendGrid activity logs but
    are never delivered to real addresses.
    """

    def __init__(self) -> None:
        self._client = SendGridAPIClient(api_key=settings.sendgrid_api_key)
        self._from_email = settings.sendgrid_from_email
        self._sandbox = settings.environment != "production"

    def send(
        self,
        to_emails: Sequence[str],
        subject: str,
        body: str,
        email_type: str,
    ) -> None:
        """
        Send a plain-text email via SendGrid.

        Raises SendGridException (or any underlying HTTP error) on
        failure. The caller (email_activities.py) is responsible for
        catching all exceptions and writing to email_failure_log.

        Args:
            to_emails: List of recipient email addresses.
            subject: Email subject line.
            body: Plain-text email body.
            email_type: Logical email type label for logging / failure
                        records (e.g. "auto_reorder_created").
        """
        message = Mail(
            from_email=self._from_email,
            to_emails=list(to_emails),
            subject=subject,
            plain_text_content=body,
        )

        if self._sandbox:
            mail_settings = MailSettings()
            sandbox = SandBoxMode()
            sandbox.enable = True
            mail_settings.sandbox_mode = sandbox
            message.mail_settings = mail_settings
            logger.debug(
                "SendGrid sandbox mode enabled for email_type=%s to=%s",
                email_type,
                to_emails,
            )

        response = self._client.send(message)
        logger.info(
            "Email sent email_type=%s to=%s status_code=%s sandbox=%s",
            email_type,
            to_emails,
            response.status_code,
            self._sandbox,
        )
