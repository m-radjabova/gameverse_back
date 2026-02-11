import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
import jwt  

from app.services.email_resent import send_email_resend

router = APIRouter(prefix="/mail", tags=["Mail"])

JWT_SECRET = os.getenv("EMAIL_TOKEN_SECRET", "change-me")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5173")

class SendVerifySchema(BaseModel):
    email: EmailStr

def make_email_token(email: str) -> str:
    payload = {
        "email": email,
        "type": "email_verify",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_email_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

@router.post("/send-verify")
def send_verify(data: SendVerifySchema, bg: BackgroundTasks):
    token = make_email_token(data.email)
    verify_link = f"{APP_BASE_URL}/verify-email?token={token}"

    subject = "Verify Your Email Address"

    html = f"""
    <h2>Hello there!</h2>
    <p>Please click the link below to verify your email address:</p>
    <p>
    <a href="{verify_link}" 
        style="display:inline-block;padding:10px 20px;background-color:#14b8a6;
                color:#ffffff;text-decoration:none;border-radius:8px;">
        Verify Email
    </a>
    </p>
    <p>If you did not create an account, you can safely ignore this email.</p>
    """

    bg.add_task(send_email_resend, data.email, subject, html, f"Verify: {verify_link}")
    return {"ok": True}

class VerifySchema(BaseModel):
    token: str

@router.post("/verify")
def verify_email(data: VerifySchema):
    try:
        payload = decode_email_token(data.token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(400, "Token eskirgan")
    except Exception:
        raise HTTPException(400, "Token noto‘g‘ri")

    if payload.get("type") != "email_verify":
        raise HTTPException(400, "Token type noto‘g‘ri")

    email = payload["email"]
    return {"verified": True, "email": email}
