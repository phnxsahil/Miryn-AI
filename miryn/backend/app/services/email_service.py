import resend
from app.config import settings

if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY

def send_password_reset(email: str, token: str):
    if not settings.RESEND_API_KEY:
        print(f"DEV MODE: Password reset link for {email}: {settings.FRONTEND_URL}/reset-password?token={token}")
        return

    reset_url = f'{settings.FRONTEND_URL}/reset-password?token={token}'
    resend.Emails.send({
        "from": "Miryn <hello@miryn.ai>",
        "to": email,
        "subject": "Reset your Miryn password",
        "html": f"""
        <p>Click below to reset your password.</p>
        <a href="{reset_url}">Reset password</a>
        <p>This link expires in 15 minutes.</p>
        """
    })

def send_welcome_email(email: str):
    if not settings.RESEND_API_KEY:
        print(f"DEV MODE: Welcome email for {email}")
        return

    resend.Emails.send({
        "from": "Sahil at Miryn <sahil@miryn.ai>",
        "to": email,
        "subject": "You're in — here's what Miryn is",
        "html": f"""
        <p>Hey there,</p>
        <p>You just created your Miryn. It starts learning about you from your first message.</p>
        <p>One thing to know: the more you share, the more useful it becomes.</p>
        <p>— Sahil</p>
        """
    })

def send_checkin(email: str, subject: str, message: str):
    if not settings.RESEND_API_KEY:
        print(f"DEV MODE: Checkin email for {email}: {subject}")
        return
    resend.Emails.send({
        "from": "Miryn <hello@miryn.ai>",
        "to": email,
        "subject": subject,
        "html": f"<p>{message}</p>"
    })
