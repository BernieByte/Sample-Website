import smtplib
from email.message import EmailMessage

from .config import Config


def send_password_reset_email(recipient, token):
    if not all((Config.SMTP_HOST, Config.SMTP_USERNAME, Config.SMTP_PASSWORD, Config.SMTP_FROM)):
        raise RuntimeError("Password reset email is not configured.")

    reset_url = f"{Config.APP_BASE_URL}/reset-password?token={token}"
    message = EmailMessage()
    message["Subject"] = "Reset your ByteNest password"
    message["From"] = Config.SMTP_FROM
    message["To"] = recipient
    message.set_content(
        "We received a request to reset your ByteNest password.\n\n"
        f"Open this link within 15 minutes:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        smtp.send_message(message)