"""
Email service — sends transactional emails via SMTP (async).
In development (SMTP_USER unset), logs email & OTP to console instead of sending.
"""
import asyncio
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from loguru import logger

from app.core.config import settings


class EmailService:

    def send_otp_email(self, to_email: str, full_name: str, otp: str) -> None:
        """Send OTP verification email — fire and forget (non-blocking)."""
        subject = "Welcome to OneGov AI — Verify Your Email"
        if not settings.SMTP_USER:
            logger.info(
                f"[DEV EMAIL] To: {to_email} | Subject: {subject} | OTP: {otp} "
                f"(expires in {settings.OTP_EXPIRE_MINUTES} minutes)"
            )
            return
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(
                self._send_async(
                    to_email=to_email,
                    subject=subject,
                    html_body=self._build_otp_html(
                        full_name=full_name,
                        otp=otp,
                        purpose="Verify your email address to activate your account",
                        expire_minutes=settings.OTP_EXPIRE_MINUTES,
                    ),
                )
            )
        except RuntimeError:
            logger.warning("No event loop — email not sent")

    def send_welcome_email(self, to_email: str, full_name: str) -> None:
        """Send Welcome email after email is successfully verified."""
        subject = "Welcome to OneGov AI 🎉"
        if not settings.SMTP_USER:
            logger.info(f"[DEV EMAIL] To: {to_email} | Subject: {subject}")
            return
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(
                self._send_async(
                    to_email=to_email,
                    subject=subject,
                    html_body=self._build_welcome_html(full_name=full_name),
                )
            )
        except RuntimeError:
            logger.warning("No event loop — email not sent")

    def send_password_reset_email(self, to_email: str, full_name: str, otp: str) -> None:
        """Send password reset OTP email."""
        subject = "OneGov AI — Reset Your Password"
        if not settings.SMTP_USER:
            logger.info(
                f"[DEV RESET] To: {to_email} | Subject: {subject} | OTP: {otp} "
                f"(expires in {settings.OTP_EXPIRE_MINUTES} minutes)"
            )
            return
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(
                self._send_async(
                    to_email=to_email,
                    subject=subject,
                    html_body=self._build_otp_html(
                        full_name=full_name,
                        otp=otp,
                        purpose="Reset your account password",
                        expire_minutes=settings.OTP_EXPIRE_MINUTES,
                    ),
                )
            )
        except RuntimeError:
            logger.warning("No event loop — email not sent")

    def send_login_notification_email(
        self,
        to_email: str,
        full_name: str,
        device: str,
        browser: str,
        ip_address: str,
        timestamp_str: str,
    ) -> None:
        """Send security notification when a user logs in from a new device/session."""
        subject = "New Login Detected — OneGov AI"
        if not settings.SMTP_USER:
            logger.info(
                f"[DEV SECURITY EMAIL] To: {to_email} | Subject: {subject} | "
                f"IP: {ip_address} | Device: {device} / {browser}"
            )
            return
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(
                self._send_async(
                    to_email=to_email,
                    subject=subject,
                    html_body=self._build_login_notification_html(
                        full_name=full_name,
                        device=device,
                        browser=browser,
                        ip_address=ip_address,
                        timestamp_str=timestamp_str,
                    ),
                )
            )
        except RuntimeError:
            logger.warning("No event loop — security email not sent")

    async def _send_async(self, to_email: str, subject: str, html_body: str) -> None:
        """Send HTML email via SMTP with TLS (aiosmtplib)."""
        try:
            import aiosmtplib
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            logger.info(f"Email sent to {to_email}: {subject}")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to send email to {to_email}: {exc}")

    @staticmethod
    def _build_otp_html(full_name: str, otp: str, purpose: str, expire_minutes: int) -> str:
        digits = "".join(
            f'<span style="display:inline-block;width:48px;height:56px;line-height:56px;'
            f'text-align:center;font-size:28px;font-weight:700;border:2px solid #3B82F6;'
            f'border-radius:10px;margin:4px;color:#3B82F6;background:rgba(59,130,246,0.05)">{d}</span>'
            for d in otp
        )
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:'Inter',Arial,sans-serif;background:#030712;margin:0;padding:32px 16px">
  <div style="max-width:540px;margin:0 auto;background:#0D1526;border-radius:20px;
              border:1px solid rgba(59,130,246,0.2);overflow:hidden;box-shadow:0 20px 40px rgba(0,0,0,0.5)">
    <div style="background:linear-gradient(135deg,#1E3A8A,#3B82F6);padding:32px;text-align:center">
      <h1 style="color:#fff;margin:0;font-size:24px;font-weight:800;letter-spacing:-0.5px">🇮🇳 OneGov AI</h1>
      <p style="color:rgba(255,255,255,0.8);margin:6px 0 0;font-size:13px">Official Public Access Portal</p>
    </div>
    <div style="padding:40px 32px">
      <p style="margin:0 0 8px;color:#F8FAFC;font-size:18px">Hello, <strong>{full_name}</strong></p>
      <p style="margin:0 0 32px;color:#94A3B8;font-size:15px;line-height:1.5">{purpose}</p>
      <div style="text-align:center;margin:0 0 32px">{digits}</div>
      <p style="margin:0;color:#64748B;font-size:13px;text-align:center">
        This code expires in <strong style="color:#94A3B8">{expire_minutes} minutes</strong>.
        Do not share this OTP with anyone.
      </p>
    </div>
    <div style="background:#050B18;padding:20px 32px;border-top:1px solid rgba(255,255,255,0.05);text-align:center">
      <p style="margin:0;color:#475569;font-size:12px">OneGov AI • Empowering Citizens with AI-driven Digital Public Infrastructure</p>
    </div>
  </div>
</body></html>"""

    @staticmethod
    def _build_welcome_html(full_name: str) -> str:
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:'Inter',Arial,sans-serif;background:#030712;margin:0;padding:32px 16px">
  <div style="max-width:540px;margin:0 auto;background:#0D1526;border-radius:20px;
              border:1px solid rgba(59,130,246,0.2);overflow:hidden">
    <div style="background:linear-gradient(135deg,#1E3A8A,#3B82F6);padding:36px;text-align:center">
      <h1 style="color:#fff;margin:0;font-size:26px;font-weight:800">Welcome to OneGov AI 🎉</h1>
    </div>
    <div style="padding:40px 32px">
      <p style="margin:0 0 16px;color:#F8FAFC;font-size:18px">Namaste, <strong>{full_name}</strong>!</p>
      <p style="margin:0 0 24px;color:#94A3B8;font-size:15px;line-height:1.6">
        Your email has been successfully verified! You now have full access to India's unified platform for citizen services, schemes, and AI assistance.
      </p>
      <div style="background:rgba(59,130,246,0.1);border-radius:12px;padding:20px;margin-bottom:28px;border:1px solid rgba(59,130,246,0.2)">
        <h4 style="margin:0 0 8px;color:#60A5FA;font-size:14px">What you can do now:</h4>
        <ul style="margin:0;padding-left:20px;color:#CBD5E1;font-size:14px;line-height:1.8">
          <li>Ask questions in 12+ Indian languages with AI Assistant</li>
          <li>Discover government welfare schemes tailored for you</li>
          <li>Apply for government digital certificates & services</li>
        </ul>
      </div>
      <div style="text-align:center">
        <a href="http://localhost:3000/dashboard" style="display:inline-block;background:#3B82F6;color:#ffffff;text-decoration:none;padding:14px 28px;border-radius:12px;font-weight:600;font-size:15px">Go to Dashboard →</a>
      </div>
    </div>
    <div style="background:#050B18;padding:20px 32px;text-align:center">
      <p style="margin:0;color:#475569;font-size:12px">OneGov AI • Government Services Access Simplified</p>
    </div>
  </div>
</body></html>"""

    @staticmethod
    def _build_login_notification_html(
        full_name: str, device: str, browser: str, ip_address: str, timestamp_str: str
    ) -> str:
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:'Inter',Arial,sans-serif;background:#030712;margin:0;padding:32px 16px">
  <div style="max-width:540px;margin:0 auto;background:#0D1526;border-radius:20px;
              border:1px solid rgba(245,158,11,0.3);overflow:hidden">
    <div style="background:linear-gradient(135deg,#78350F,#F59E0B);padding:28px 32px">
      <h1 style="color:#fff;margin:0;font-size:20px">🛡️ Security Alert: New Login Detected</h1>
    </div>
    <div style="padding:36px 32px">
      <p style="margin:0 0 12px;color:#F8FAFC;font-size:16px">Hello, <strong>{full_name}</strong></p>
      <p style="margin:0 0 24px;color:#94A3B8;font-size:14px;line-height:1.5">
        We detected a successful login to your OneGov AI account from a new session or device:
      </p>
      <table style="width:100%;border-collapse:collapse;margin-bottom:28px;background:rgba(255,255,255,0.03);border-radius:10px">
        <tr><td style="padding:10px 14px;color:#64748B;font-size:13px">Time:</td><td style="padding:10px 14px;color:#F8FAFC;font-size:13px;font-weight:600">{timestamp_str}</td></tr>
        <tr><td style="padding:10px 14px;color:#64748B;font-size:13px">Device / OS:</td><td style="padding:10px 14px;color:#F8FAFC;font-size:13px;font-weight:600">{device}</td></tr>
        <tr><td style="padding:10px 14px;color:#64748B;font-size:13px">Browser:</td><td style="padding:10px 14px;color:#F8FAFC;font-size:13px;font-weight:600">{browser}</td></tr>
        <tr><td style="padding:10px 14px;color:#64748B;font-size:13px">IP Address:</td><td style="padding:10px 14px;color:#F8FAFC;font-size:13px;font-weight:600">{ip_address}</td></tr>
      </table>
      <p style="margin:0 0 20px;color:#EF4444;font-size:13px">
        If this was not you, your account may be compromised. Please reset your password immediately.
      </p>
      <div style="text-align:center">
        <a href="http://localhost:3000/forgot-password" style="display:inline-block;background:#EF4444;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:10px;font-weight:600;font-size:14px">Reset Password Now</a>
      </div>
    </div>
    <div style="background:#050B18;padding:18px 32px;text-align:center">
      <p style="margin:0;color:#475569;font-size:12px">OneGov AI Security Team</p>
    </div>
  </div>
</body></html>"""

