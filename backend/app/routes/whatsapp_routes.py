from datetime import datetime, timedelta
import os
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, crud
from app.core.config import settings
from app.core.security import decode_jwt
from app.services.twilio_service import (
    send_whatsapp_message,
    make_verification_code,
    validate_twilio_signature
)
from app.services.calendar_service import fetch_today_events_for_user
from app.db.models import User


router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# -----------------------------
# Request Models
# -----------------------------
class LinkRequest(BaseModel):
    number: str  # e.g. +919876543210

class VerifyRequest(BaseModel):
    number: str
    code: str

# -----------------------------
# Endpoints
# -----------------------------

@router.post("/link")
async def link_whatsapp(req: LinkRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    """Authenticated user links a WhatsApp number (sends verification code)."""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        raise HTTPException(401, "Invalid token")

    email = data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")

    # Validate and normalize number
    number = req.number.strip()
    if not number.startswith("+"):
        raise HTTPException(400, "Phone number must be in E.164 format (e.g. +9198...)")
    whatsapp_to = f"whatsapp:{number}"

    # Generate verification code
    code = make_verification_code()
    crud.set_whatsapp_verification(db, user, code, expires_in_minutes=10)

    try:
        send_whatsapp_message(whatsapp_to, f"Your ProjectAria.PA verification code: {code}")
    except Exception as e:
        raise HTTPException(500, f"Twilio send error: {str(e)}")

    return {"status": "sent"}


@router.post("/verify")
async def verify_whatsapp(req: VerifyRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    """User posts back the verification code to confirm their WhatsApp number."""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        raise HTTPException(401, "Invalid token")

    email = data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")

    if user.whatsapp_verify_code != req.code:
        raise HTTPException(400, "Invalid verification code")

    if user.whatsapp_verify_expires and user.whatsapp_verify_expires < datetime.utcnow():
        raise HTTPException(400, "Verification code expired")

    # success
    user.whatsapp_no = req.number.strip()
    user.whatsapp_verified = True
    user.whatsapp_verify_code = None
    user.whatsapp_verify_expires = None
    db.commit()
    return {"status": "verified"}


@router.post("/webhook")
async def whatsapp_webhook(request: Request, x_twilio_signature: str = Header(None), db: Session = Depends(get_db)):
    """Twilio webhook for incoming WhatsApp messages."""
    raw_body = await request.form()
    params = dict(raw_body)
    signature = x_twilio_signature

    if not validate_twilio_signature(settings.TWILIO_WEBHOOK_URL, params, signature):
        raise HTTPException(403, "Invalid Twilio signature")

    from_number = params.get("From")  # e.g. "whatsapp:+919876543210"
    body = params.get("Body", "").strip()
    print(f"Incoming WhatsApp from {from_number}: {body}")

    incoming = from_number.replace("whatsapp:", "").strip()
    user = crud.get_user_by_whatsapp_no(db, incoming)

    if not user:
        send_whatsapp_message(from_number,
            "Hi — to link your WhatsApp with ProjectAria.PA, open the web app and connect your number in Integration → Connect WhatsApp."
        )
        return "OK"

    lower = body.lower()
    if "calendar" in lower:
        events, message = await fetch_today_events_for_user(user)
        if events is None:
            send_whatsapp_message(from_number, f"Sorry, I couldn't access your calendar: {message}")
        elif not events:
            send_whatsapp_message(from_number, "You have no events in the next 24 hours.")
        else:
            send_whatsapp_message(from_number, "Here are your upcoming events:\n\n" + message)
        return "OK"

    send_whatsapp_message(from_number, "Hello! Commands: 'calendar' → today's events. More features coming soon.")
    return "OK"

@router.post("/unlink")
async def unlink_whatsapp(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Disconnect a linked WhatsApp number"""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    import jwt as pyjwt
    token = authorization.replace("Bearer ", "")
    data = pyjwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"], options={"verify_exp": False})
    email = data.get("sub")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.whatsapp_no = None
    user.whatsapp_verified = False
    db.commit()

    return {"status": "unlinked"}
