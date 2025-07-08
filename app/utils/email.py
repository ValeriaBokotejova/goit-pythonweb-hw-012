# pylint: disable=E0401,E0611
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.core.config import settings

# Email template for verification
TEMPLATE_PATH = Path(__file__).parent / "templates" / "verify_email.html"
RESET_TEMPLATE_PATH = Path(__file__).parent / "templates" / "reset_password.html"


def load_template() -> str:
    """Load the HTML template for the email."""
    if TEMPLATE_PATH.exists():
        return TEMPLATE_PATH.read_text()
    raise FileNotFoundError("Email template not found.")


def send_verification_email(to_email: str, token: str):
    """Send verification email with a confirmation link."""
    subject = "Verify your email address"
    from_email = settings.mail_username
    password = settings.mail_password
    smtp_server = settings.mail_server
    smtp_port = settings.mail_port

    verification_link = f"{settings.frontend_verify_url}?token={token}"
    html_template = TEMPLATE_PATH.read_text()
    html_content = html_template.replace("{{ verification_link }}", verification_link)

    # Construct the email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, message.as_string())
    except Exception as e:
        raise RuntimeError(f"Failed to send verification email: {e}") from e


def send_password_reset_email(to_email: str, token: str):
    subject = "Password Reset Request"
    from_email = settings.mail_username
    password = settings.mail_password
    smtp_server = settings.mail_server
    smtp_port = settings.mail_port

    reset_link = f"{settings.frontend_reset_url}?token={token}"

    if RESET_TEMPLATE_PATH.exists():
        html_template = RESET_TEMPLATE_PATH.read_text()
    else:
        raise FileNotFoundError("Reset password email template not found.")

    html_content = html_template.replace("{{ reset_link }}", reset_link)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email

    part_html = MIMEText(html_content, "html")
    message.attach(part_html)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, message.as_string())
    except Exception as e:
        raise RuntimeError(f"Failed to send password reset email: {e}") from e
