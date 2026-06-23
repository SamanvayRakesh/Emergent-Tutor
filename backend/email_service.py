"""Email service using Resend for transactional emails."""
import asyncio
import os
import resend
from core import logger

resend.api_key = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "https://neural-exam-prep.preview.emergentagent.com")


async def send_verification_email(email: str, name: str, token: str) -> bool:
    verify_url = f"{FRONTEND_BASE_URL}/verify-email?token={token}"
    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#111118;border:1px solid rgba(255,255,255,0.08);border-radius:16px;overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#dc2626,#1e40af);padding:32px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:900;letter-spacing:-0.5px;">AceIt AI</h1>
            <p style="margin:8px 0 0;color:rgba(255,255,255,0.75);font-size:13px;">CBSE AI Tutor</p>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 32px;">
            <h2 style="margin:0 0 16px;color:#ffffff;font-size:20px;">Verify your email, {name.split()[0] if name else 'there'}!</h2>
            <p style="margin:0 0 24px;color:#a1a1aa;font-size:15px;line-height:1.6;">
              You're one step away from unlocking your personalised CBSE AI tutor. Click the button below to verify your email address.
            </p>
            <table cellpadding="0" cellspacing="0">
              <tr>
                <td style="border-radius:10px;background:#dc2626;">
                  <a href="{verify_url}" style="display:inline-block;padding:14px 32px;color:#ffffff;font-weight:700;font-size:15px;text-decoration:none;letter-spacing:0.3px;">
                    Verify Email Address
                  </a>
                </td>
              </tr>
            </table>
            <p style="margin:24px 0 0;color:#71717a;font-size:13px;">
              This link expires in <strong style="color:#a1a1aa;">24 hours</strong>. If you didn't create an account, you can safely ignore this email.
            </p>
            <hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:28px 0;">
            <p style="margin:0;color:#52525b;font-size:12px;">
              Having trouble? Copy this link:<br>
              <span style="color:#818cf8;word-break:break-all;">{verify_url}</span>
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px;border-top:1px solid rgba(255,255,255,0.05);text-align:center;">
            <p style="margin:0;color:#3f3f46;font-size:12px;">© 2025 AceIt AI · AI-powered CBSE tutoring</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    params = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": "Verify your AceIt AI account",
        "html": html,
    }
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Verification email sent to {email}, id={result.get('id')}")
        return True
    except Exception as e:
        err_str = str(e)
        logger.error(f"Failed to send verification email to {email}: {e}")
        # Resend sandbox restriction: only owner's email can receive in test mode
        # User needs to verify a domain at resend.com/domains to enable sending to all users
        if "testing emails to your own email" in err_str.lower() or "domain" in err_str.lower():
            logger.warning(
                "RESEND SANDBOX MODE: Email delivery restricted to account owner's email. "
                "To send verification emails to all users, verify a domain at https://resend.com/domains"
            )
        return False


async def send_welcome_email(email: str, name: str) -> bool:
    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#111118;border:1px solid rgba(255,255,255,0.08);border-radius:16px;overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#dc2626,#1e40af);padding:32px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:900;">AceIt AI</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 32px;">
            <h2 style="margin:0 0 12px;color:#ffffff;font-size:20px;">You're verified!</h2>
            <p style="margin:0 0 20px;color:#a1a1aa;font-size:15px;line-height:1.6;">
              Welcome to AceIt AI, {name.split()[0] if name else 'there'}! Your account is ready.
              Start your personalised CBSE learning journey now.
            </p>
            <p style="margin:0;color:#71717a;font-size:13px;">Good luck with your exams!</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    params = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": "Welcome to AceIt AI — you're all set!",
        "html": html,
    }
    try:
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.error(f"Welcome email error: {e}")
        return False
