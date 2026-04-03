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

async def send_password_reset_email(to_email: str, reset_url: str):
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height:1.6; color:#333; max-width:600px; margin:0 auto;">
            <div style="background-color:#f8f9fa; padding:30px; border-radius:10px;">
                <h2 style="color:#6C63FF; margin-bottom:20px;">Reset Your Password</h2>
                <p>Hi there,</p>
                <p>We received a request to reset your upSkillmee account password. Click the button below to set a new password.</p>
                <p style="text-align:center; margin: 30px 0;">
                    <a href="{reset_url}"
                       style="background-color:#6C63FF;color:white;padding:14px 28px;text-decoration:none;border-radius:6px;font-weight:bold;font-size:16px;">
                       Reset Password
                    </a>
                </p>
                <p style="color:#666; font-size:14px;">
                    This link will expire in <strong>15 minutes</strong>. If you did not request a password reset, you can safely ignore this email — your password will not be changed.
                </p>
                <p style="color:#999; font-size:12px; margin-top:30px;">
                    If the button above doesn't work, copy and paste this URL into your browser:<br>
                    <a href="{reset_url}" style="color:#6C63FF;">{reset_url}</a>
                </p>
                <p>Best regards,<br>upSkillmee Team</p>
            </div>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Reset Your upSkillmee Password",
        recipients=[to_email],
        body=html_body,
        subtype=MessageType.html
    )

    fm = FastMail(get_connection_config())
    try:
        await fm.send_message(message)
        logger.info(f"Password reset email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
        raise


async def send_email_verification_token_email(to_email: str, verify_url: str):
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height:1.6; color:#333; max-width:600px; margin:0 auto;">
            <div style="background-color:#f8f9fa; padding:30px; border-radius:10px;">
                <h2 style="color:#6C63FF; margin-bottom:20px;">Verify Your Email Address</h2>
                <p>Hi there,</p>
                <p>Thanks for signing up for upSkillmee! Please verify your email address to access the platform.</p>
                <p style="text-align:center; margin: 30px 0;">
                    <a href="{verify_url}"
                       style="background-color:#6C63FF;color:white;padding:14px 28px;text-decoration:none;border-radius:6px;font-weight:bold;font-size:16px;">
                       Verify Email
                    </a>
                </p>
                <p style="color:#666; font-size:14px;">
                    This link will expire in <strong>24 hours</strong>. If you did not sign up for upSkillmee, you can safely ignore this email.
                </p>
                <p style="color:#999; font-size:12px; margin-top:30px;">
                    If the button above doesn't work, copy and paste this URL into your browser:<br>
                    <a href="{verify_url}" style="color:#6C63FF;">{verify_url}</a>
                </p>
                <p>Best regards,<br>upSkillmee Team</p>
            </div>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Verify your upSkillmee email address",
        recipients=[to_email],
        body=html_body,
        subtype=MessageType.html
    )

    fm = FastMail(get_connection_config())
    try:
        await fm.send_message(message)
        logger.info(f"Email verification token sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email verification to {to_email}: {str(e)}")
        raise


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
