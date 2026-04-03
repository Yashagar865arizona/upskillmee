from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import logging
from app.config.settings import settings  

logger = logging.getLogger("email_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def get_connection_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASS,
        MAIL_FROM=settings.SMTP_FROM,
        MAIL_SERVER=settings.SMTP_SERVER,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_STARTTLS=settings.SMTP_TLS,
        MAIL_SSL_TLS=settings.SMTP_SSL,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )

async def send_verification_email(to_email: str, website_url: str):
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height:1.6; color:#333;">
            <h2 style="color:#4CAF50;">Your email is approved! 🎉</h2>
            <p>Hi there,</p>
            <p>Your email has been approved by our admin. You can now log in and start exploring the platform.</p>
            <p style="text-align:center; margin: 30px 0;">
                <a href="{website_url}" 
                   style="background-color:#4CAF50;color:white;padding:12px 25px;text-decoration:none;border-radius:5px;font-weight:bold;">
                   Login Now
                </a>
            </p>
            <p>Best regards,<br>upSkillmee Team</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Welcome to upSkillmee! Your Email is Approved 🎉",
        recipients=[to_email],
        body=html_body,
        subtype=MessageType.html
    )

    fm = FastMail(get_connection_config())
    try:
        await fm.send_message(message)
        logger.info(f"Verification email successfully sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {to_email}: {str(e)}")
