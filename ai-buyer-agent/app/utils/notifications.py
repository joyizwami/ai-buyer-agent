"""Optional transaction notifications."""

import smtplib
from email.message import EmailMessage

from app.config import get_settings
from app.models.transaction import Transaction
from app.utils.logger import get_logger

logger = get_logger(__name__)


def send_receipt_email(transaction: Transaction) -> None:
    """Send a payment receipt when SMTP is configured; otherwise log a setup hint."""
    recipient = transaction.metadata.get("receipt_email")
    settings = get_settings()
    if not recipient:
        return
    if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password or not settings.smtp_from_email:
        logger.warning("Receipt email skipped: SMTP configuration is incomplete")
        return

    message = EmailMessage()
    message["Subject"] = f"Purchase receipt - {transaction.product_name}"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(
        f"Your payment was completed successfully.\n\n"
        f"Product: {transaction.product_name}\n"
        f"Amount: INR {transaction.amount_inr:,.2f}\n"
        f"Transaction ID: {transaction.id}\n"
        f"Payment ID: {transaction.razorpay_payment.id if transaction.razorpay_payment else 'pending'}\n"
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        logger.info("Receipt email sent", extra={"transaction_id": transaction.id, "recipient": recipient})
    except Exception as error:
        logger.error("Receipt email failed", extra={"transaction_id": transaction.id, "error": str(error)})