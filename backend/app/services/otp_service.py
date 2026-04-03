from datetime import datetime, timedelta
import random
import string
import re
try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None  # type: ignore[assignment,misc]

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:
    SendGridAPIClient = None  # type: ignore[assignment,misc]
    Mail = None  # type: ignore[assignment,misc]

from app.config.settings import settings
from app.utils.phone import format_phone_number
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

otp_store = {}
OTP_EXPIRY_MINUTES = 5


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


def is_email(value: str) -> bool:
    """Check if the identifier is an email address."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", value) is not None


def send_otp(identifier: str) -> tuple[bool, str]:
    """
    Send OTP via email or SMS.
    Returns: (success, otp)
    """
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    otp_store[identifier] = {"otp": otp, "expires_at": expires_at}

    if is_email(identifier):
        # Send via email
        subject = "Your OTP Code"
        content = f"Your OTP code is: {otp}. It will expire in {OTP_EXPIRY_MINUTES} minutes."
        try:
            success = send_email(identifier, subject, content)
            if not success:
                raise Exception("Email sending failed")
            return True, otp
        except Exception as e:
            print(f"[ERROR] Failed to send email OTP: {e}")
            return False, otp
    else:
        # Send via SMS
        try:
            formatted_number = format_phone_number(identifier)
            client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"Your OTP code is: {otp}. It will expire in {OTP_EXPIRY_MINUTES} minutes.",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=formatted_number
            )
            return True, otp
        except Exception as e:
            print(f"[ERROR] Failed to send SMS OTP: {e}")
            return False, otp


def verify_otp(identifier: str, otp: str) -> bool:
    """
    Verify the OTP for email or phone.
    Returns True if valid, False otherwise.
    """
    record = otp_store.get(identifier)
    if not record:
        return False
    if record["otp"] != otp:
        return False
    if datetime.utcnow() > record["expires_at"]:
        return False
    return True

# sms

def send_sms(to_number: str, body: str):
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print("Twilio not configured")
        return False
    try:
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(body=body, from_=settings.TWILIO_PHONE_NUMBER, to=to_number)
        return True
    except Exception as e:
        print("Send SMS error:", e)
        return False
    

# def send_email(to_email: str, subject: str, content: str) -> bool:
#     if not settings.SENDGRID_API_KEY or not settings.EMAIL_USER:
#         print("sendGrid or sender email not configured")
#         return False
#     try:
#         message = Mail(
#             from_email=settings.EMAIL_USER,
#             to_emails=to_email,
#             subject=subject,
#             plain_text_content=content,
#             html_content=content
#         )
#         sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
#         sg_client.send(message)
#         return True
#     except Exception as e:
#         print(f"Send email error: {e}")
#         return False


def send_email(to_email: str, subject: str, content: str) -> bool:
    """
    Send an email via SMTP.
    Returns True if sent successfully, False otherwise.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        print("SMTP credentials not configured")
        return False

    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_FROM
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach both plain text and HTML content
        # msg.attach(MIMEText(content, 'plain'))
        # msg.attach(MIMEText(f"<p>{content}</p>", 'html'))
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(content, "plain"))
        msg.attach(MIMEText(f"<p>{content}</p>", "html"))


        # Connect to SMTP server and send email
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        print(f"[ERROR] Send email via SMTP failed: {e}")
        return False
