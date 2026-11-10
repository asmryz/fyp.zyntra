"""
Sends emails through the SMTP account configured in .env.

SMTP can only tell us whether the mail server accepted a message. It cannot
reliably confirm that a mailbox exists (Gmail usually accepts the message and
sends a bounce later). That is why accounts are only activated after the
user enters the code from the email.
"""
import json
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from app.config import settings
from app.core.security import utcnow

logger = logging.getLogger("zyntra.email")

OUTBOX_DIR = Path(__file__).resolve().parents[2] / "dev_outbox"


class EmailDeliveryError(Exception):
    def __init__(self, message, recipient_rejected=False):
        super().__init__(message)
        self.recipient_rejected = recipient_rejected


def _save_to_outbox(to_email, subject, html_body, text_body):
    """Local testing only: write the email to a JSON file instead of sending it."""
    OUTBOX_DIR.mkdir(exist_ok=True)
    timestamp = utcnow().strftime("%Y%m%dT%H%M%S%f")
    path = OUTBOX_DIR / f"{timestamp}_{to_email.replace('@', '_at_')}.json"
    path.write_text(
        json.dumps({"to": to_email, "subject": subject, "text": text_body, "html": html_body}, indent=2),
        encoding="utf-8",
    )


def send_email(to_email: str, subject: str, html_body: str, text_body: str):
    if settings.email_backend == "outbox":
        _save_to_outbox(to_email, subject, html_body, text_body)
        return

    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from_email]):
        raise EmailDeliveryError("Email service is not configured.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.smtp_from_name, settings.smtp_from_email))
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()
    try:
        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20, context=context)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20)
            server.starttls(context=context)
        with server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except smtplib.SMTPRecipientsRefused:
        # Log only the domain, never credentials or full addresses
        logger.warning("SMTP server refused recipient at domain %s", to_email.split("@")[-1])
        raise EmailDeliveryError(
            "The email server rejected this address. Please check that it is correct.", recipient_rejected=True
        )
    except (smtplib.SMTPException, OSError) as error:
        logger.error("Email delivery failed: %s", type(error).__name__)
        raise EmailDeliveryError("We could not send the email right now. Please try again in a few minutes.")
