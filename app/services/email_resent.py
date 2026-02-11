import os
import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM = os.getenv("RESEND_FROM")

def send_email_resend(to_email: str, subject: str, html: str, text: str | None = None):
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set")

    payload = {
        "from": RESEND_FROM,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    if r.status_code >= 400:
        raise RuntimeError(f"Resend error: {r.status_code} - {r.text}")

    return r.json()  
