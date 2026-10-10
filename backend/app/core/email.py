"""
Minimal email delivery for notifications.

* SMTP_HOST configured  -> real email via SMTP (any provider: SendGrid SMTP,
  Gmail app password, AWS SES SMTP, Mailgun...).
* SMTP_HOST not set     -> the message is logged instead (development).

Sending happens on a background thread and never raises, so a slow or broken
mail server can never fail or delay an API request.
"""

import logging
import smtplib
import threading
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("trustshare.email")


def _deliver(to_address: str, subject: str, body: str) -> None:
    settings = get_settings()

    if not settings.SMTP_HOST:
        logger.info("DEV EMAIL to=%s subject=%r\n%s", to_address, subject, body)
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
    except Exception:  # noqa: BLE001 - delivery must never break the caller
        logger.exception("Failed to send email to %s", to_address)


def send_email_background(to_address: str, subject: str, body: str) -> None:
    threading.Thread(
        target=_deliver, args=(to_address, subject, body), daemon=True
    ).start()
