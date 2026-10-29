import json
import smtplib
from email.message import EmailMessage
from urllib.request import Request, urlopen

from flask import current_app


def send_password_reset_email(recipient, token):
    config = current_app.config
    reset_url = f"{config['APP_BASE_URL']}/reset-password?token={token}"
    body = (
        "We received a request to reset your ByteNest password.\n\n"
        f"Open this link within 15 minutes:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )

    if config.get("BREVO_API_KEY"):
        if not config.get("EMAIL_FROM"):
            raise RuntimeError("The Brevo sender email is not configured.")
        payload = json.dumps({
            "sender": {"name": "ByteNest", "email": config["EMAIL_FROM"]},
            "to": [{"email": recipient}],
            "subject": "Reset your ByteNest password",
            "textContent": body,
        }).encode("utf-8")
        request = Request(
            "https://api.brevo.com/v3/smtp/email",
            data=payload,
            headers={
                "api-key": config["BREVO_API_KEY"],
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=15):
            return

    if not all((
        config.get("SMTP_HOST"),
        config.get("SMTP_USERNAME"),
        config.get("SMTP_PASSWORD"),
        config.get("SMTP_FROM"),
    )):
        raise RuntimeError("Password reset email is not configured.")

    message = EmailMessage()
    message["Subject"] = "Reset your ByteNest password"
    message["From"] = config["SMTP_FROM"]
    message["To"] = recipient
    message.set_content(body)

    with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"], timeout=15) as smtp:
        smtp.starttls()
        smtp.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
        smtp.send_message(message)
