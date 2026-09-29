"""Email notification and verification service for Chimera v3.0.

Supports SMTP (Gmail, SendGrid, Mailgun, custom relays) with STARTTLS/SSL,
and includes an automatic development fallback that outputs OTPs to the console
so local testing is never blocked when SMTP credentials are not yet configured.
"""

import html
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any

from backend.core.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_USE_TLS,
    SMTP_USE_SSL,
    OTP_EXPIRY_SECONDS,
)

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    """Return True if SMTP server and credentials are set in environment."""
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def _build_html_body(name: str, otp_code: str, expiry_minutes: int) -> str:
    """Generate high-contrast, modern HTML email template for OTP code."""
    safe_name = html.escape(name.strip()) if name else "Creator"
    safe_otp = html.escape(otp_code.strip())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chimera Verification Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #08090c; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f0f0f5;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #08090c; padding: 40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 520px; background-color: #11131a; border-radius: 16px; border: 1px solid #232734; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);" cellspacing="0" cellpadding="0">
          
          <!-- Header / Brand -->
          <tr>
            <td style="padding: 36px 36px 20px 36px; text-align: center; border-bottom: 1px solid #1c202c; background: radial-gradient(circle at 50% 0%, rgba(0, 212, 170, 0.12), transparent 70%);">
              <div style="display: inline-block; width: 44px; height: 44px; line-height: 44px; border-radius: 12px; background: #e8402c; color: #ffffff; font-weight: 900; font-size: 22px; text-align: center; box-shadow: 0 4px 14px rgba(232, 64, 44, 0.4);">
                🦁
              </div>
              <h1 style="margin: 16px 0 4px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff;">CHIMERA STUDIO</h1>
              <p style="margin: 0; font-size: 13px; color: #00d4aa; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">AI Video Automation Engine</p>
            </td>
          </tr>

          <!-- Content Body -->
          <tr>
            <td style="padding: 32px 36px 24px 36px;">
              <h2 style="margin: 0 0 12px 0; font-size: 18px; font-weight: 700; color: #ffffff;">Verify your email address</h2>
              <p style="margin: 0 0 24px 0; font-size: 14px; line-height: 1.6; color: #a2a8ba;">
                Hello <strong style="color: #ffffff;">{safe_name}</strong>,<br>
                Thank you for joining Chimera. Please enter the verification code below to verify your email and activate your account.
              </p>

              <!-- OTP Display Box -->
              <div style="background-color: #0b0c10; border: 1px solid #293042; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 24px;">
                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #6e768e; margin-bottom: 8px; font-weight: 600;">Verification Code</div>
                <div style="font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace; font-size: 34px; font-weight: 800; letter-spacing: 10px; color: #00d4aa; text-indent: 10px;">
                  {safe_otp}
                </div>
              </div>

              <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #81889c;">
                ⏱️ This code will expire in <strong style="color: #ffffff;">{expiry_minutes} minutes</strong>. For security reasons, do not share this code with anyone.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 36px 32px 36px; border-top: 1px solid #1c202c; background-color: #0d0f15; text-align: center;">
              <p style="margin: 0 0 6px 0; font-size: 12px; color: #5a6074;">
                If you did not request this email, please ignore it. Your account will not be created without verification.
              </p>
              <p style="margin: 0; font-size: 11px; color: #434857;">
                © 2026 Chimera AI Studio. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _build_text_body(name: str, otp_code: str, expiry_minutes: int) -> str:
    """Generate plain text fallback body for email clients without HTML."""
    greeting = f"Hello {name}," if name else "Hello,"
    return (
        f"{greeting}\n\n"
        f"Your Chimera verification code is:\n\n"
        f"    {otp_code}\n\n"
        f"This code is valid for {expiry_minutes} minutes.\n"
        f"If you did not request this code, you can safely ignore this email.\n\n"
        f"— Chimera AI Studio Team"
    )


def send_otp_email(to_email: str, otp_code: str, name: str = "") -> Dict[str, Any]:
    """Send verification OTP to user's email address.

    If SMTP is configured, sends a real email.
    If SMTP is NOT configured or fails in local development, logs prominently
    to the terminal console and returns dev_mode=True so local testing works seamlessly.
    """
    to_email = to_email.strip().lower()
    expiry_minutes = max(1, int(OTP_EXPIRY_SECONDS // 60))

    if not is_smtp_configured():
        # Dev fallback: Print prominently to terminal and logger
        banner = (
            "\n"
            "╔══════════════════════════════════════════════════════════════════════╗\n"
            "║             CHIMERA EMAIL VERIFICATION (DEV / LOCAL MODE)            ║\n"
            "╠══════════════════════════════════════════════════════════════════════╣\n"
            f"║ Recipient : {to_email:<56} ║\n"
            f"║ OTP Code  : {otp_code:<56} ║\n"
            f"║ Expiry    : {expiry_minutes} minutes{' ' * 46} ║\n"
            "║ Status    : Console simulated (Set SMTP_* in .env for real emails)   ║\n"
            "╚══════════════════════════════════════════════════════════════════════╝\n"
        )
        print(banner, flush=True)
        logger.info(f"[DEV OTP] Sent verification code {otp_code} to {to_email}")
        return {
            "sent": True,
            "dev_mode": True,
            "otp": otp_code,
            "message": "Verification code logged to server console (SMTP not configured).",
        }

    # Real SMTP delivery
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Chimera Verification Code: {otp_code}"
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        text_part = MIMEText(_build_text_body(name, otp_code, expiry_minutes), "plain", "utf-8")
        html_part = MIMEText(_build_html_body(name, otp_code, expiry_minutes), "html", "utf-8")

        msg.attach(text_part)
        msg.attach(html_part)

        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())

        logger.info(f"Verification email with OTP sent to {to_email}")
        return {
            "sent": True,
            "dev_mode": False,
            "message": "Verification code sent to your email inbox.",
        }

    except Exception as e:
        logger.error(f"Failed to send email via SMTP ({e}). Falling back to dev logger.")
        fallback_banner = (
            "\n"
            "⚠️ [SMTP WARNING: Email delivery failed, logging fallback OTP]\n"
            f"   Error    : {e}\n"
            f"   Recipient: {to_email}\n"
            f"   OTP Code : {otp_code}\n"
        )
        print(fallback_banner, flush=True)
        return {
            "sent": False,
            "dev_mode": True,
            "otp": otp_code,
            "error": str(e),
            "message": "SMTP delivery failed. Verification code logged to server console.",
        }


def _build_reset_html_body(name: str, otp_code: str, expiry_minutes: int) -> str:
    """Generate high-contrast HTML email template for password reset OTP."""
    safe_name = html.escape(name.strip()) if name else "Creator"
    safe_otp = html.escape(otp_code.strip())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset Your Chimera Password</title>
</head>
<body style="margin: 0; padding: 0; background-color: #08090c; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f0f0f5;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #08090c; padding: 40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 520px; background-color: #11131a; border-radius: 16px; border: 1px solid #232734; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);" cellspacing="0" cellpadding="0">
          <tr>
            <td style="padding: 36px 36px 20px 36px; text-align: center; border-bottom: 1px solid #1c202c; background: radial-gradient(circle at 50% 0%, rgba(232, 64, 44, 0.15), transparent 70%);">
              <div style="display: inline-block; width: 44px; height: 44px; line-height: 44px; border-radius: 12px; background: #e8402c; color: #ffffff; font-weight: 900; font-size: 22px; text-align: center; box-shadow: 0 4px 14px rgba(232, 64, 44, 0.4);">
                🦁
              </div>
              <h1 style="margin: 16px 0 4px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff;">CHIMERA STUDIO</h1>
              <p style="margin: 0; font-size: 13px; color: #e8402c; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Password Reset Request</p>
            </td>
          </tr>

          <tr>
            <td style="padding: 32px 36px 24px 36px;">
              <h2 style="margin: 0 0 12px 0; font-size: 18px; font-weight: 700; color: #ffffff;">Reset your account password</h2>
              <p style="margin: 0 0 24px 0; font-size: 14px; line-height: 1.6; color: #a2a8ba;">
                Hello <strong style="color: #ffffff;">{safe_name}</strong>,<br>
                We received a request to reset your Chimera password. Use the verification code below to authorize a new password for your account.
              </p>

              <div style="background-color: #0b0c10; border: 1px solid #293042; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 24px;">
                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #6e768e; margin-bottom: 8px; font-weight: 600;">Reset Code</div>
                <div style="font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace; font-size: 34px; font-weight: 800; letter-spacing: 10px; color: #e8402c; text-indent: 10px;">
                  {safe_otp}
                </div>
              </div>

              <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #81889c;">
                ⏱️ This code will expire in <strong style="color: #ffffff;">{expiry_minutes} minutes</strong>. If you did not request this password reset, please ignore this email and your password will remain unchanged.
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding: 20px 36px 32px 36px; border-top: 1px solid #1c202c; background-color: #0d0f15; text-align: center;">
              <p style="margin: 0; font-size: 11px; color: #434857;">
                © 2026 Chimera AI Studio. Security notification.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _build_reset_text_body(name: str, otp_code: str, expiry_minutes: int) -> str:
    """Generate plain text fallback body for password reset."""
    greeting = f"Hello {name}," if name else "Hello,"
    return (
        f"{greeting}\n\n"
        f"We received a request to reset your Chimera account password.\n\n"
        f"Your password reset verification code is:\n\n"
        f"    {otp_code}\n\n"
        f"This code will expire in {expiry_minutes} minutes.\n"
        f"If you did not request a password reset, you can safely ignore this email.\n\n"
        f"— Chimera AI Studio Security Team"
    )


def send_password_reset_email(to_email: str, otp_code: str, name: str = "") -> Dict[str, Any]:
    """Send password reset OTP to user's email address."""
    to_email = to_email.strip().lower()
    expiry_minutes = max(1, int(OTP_EXPIRY_SECONDS // 60))

    if not is_smtp_configured():
        banner = (
            "\n"
            "╔══════════════════════════════════════════════════════════════════════╗\n"
            "║             CHIMERA PASSWORD RESET (DEV / LOCAL MODE)                ║\n"
            "╠══════════════════════════════════════════════════════════════════════╣\n"
            f"║ Recipient : {to_email:<56} ║\n"
            f"║ Reset OTP : {otp_code:<56} ║\n"
            f"║ Expiry    : {expiry_minutes} minutes{' ' * 46} ║\n"
            "║ Status    : Console simulated (Set SMTP_* in .env for real emails)   ║\n"
            "╚══════════════════════════════════════════════════════════════════════╝\n"
        )
        print(banner, flush=True)
        logger.info(f"[DEV RESET OTP] Sent password reset code {otp_code} to {to_email}")
        return {
            "sent": True,
            "dev_mode": True,
            "otp": otp_code,
            "message": "Reset code logged to server console (SMTP not configured).",
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Chimera Password Reset Code: {otp_code}"
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        text_part = MIMEText(_build_reset_text_body(name, otp_code, expiry_minutes), "plain", "utf-8")
        html_part = MIMEText(_build_reset_html_body(name, otp_code, expiry_minutes), "html", "utf-8")

        msg.attach(text_part)
        msg.attach(html_part)

        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())

        logger.info(f"Password reset email sent to {to_email}")
        return {
            "sent": True,
            "dev_mode": False,
            "message": "Password reset code sent to your email inbox.",
        }

    except Exception as e:
        logger.error(f"Failed to send password reset email via SMTP ({e}).")
        fallback_banner = (
            "\n"
            "⚠️ [SMTP WARNING: Password reset email failed, logging fallback OTP]\n"
            f"   Error    : {e}\n"
            f"   Recipient: {to_email}\n"
            f"   Reset OTP: {otp_code}\n"
        )
        print(fallback_banner, flush=True)
        return {
            "sent": False,
            "dev_mode": True,
            "otp": otp_code,
            "error": str(e),
            "message": "SMTP delivery failed. Reset code logged to server console.",
        }

