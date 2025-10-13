# app/routes/whatsapp_routes.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from app.db import get_db, crud
from app.db.models import User
from app.core.config import settings
from app.core.security import decode_jwt
from app.core.logging_config import user_context
from app.services.twilio_service import (
    send_whatsapp_message,
    make_verification_code,
    validate_twilio_signature,
)
from app.services.calendar_service import fetch_today_events_for_user

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
logger = logging.getLogger("ProjectAria.WhatsApp")


# -----------------------------
# 📘 Request Models
# -----------------------------
class LinkRequest(BaseModel):
    number: str  # e.g. +919876543210


class VerifyRequest(BaseModel):
    number: str
    code: str


# -----------------------------
# 🔗 Link WhatsApp Number
# -----------------------------
@router.post("/link")
async def link_whatsapp(req: LinkRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    """Authenticated user links a WhatsApp number (sends verification code)."""
    if not authorization:
        logger.warning("Missing Authorization header in /link")
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        logger.warning("Invalid JWT token in /link")
        raise HTTPException(401, "Invalid token")

    email = data.get("sub")
    user_context.set(email)
    user = crud.get_user_by_email(db, email)
    if not user:
        logger.error(f"User not found for email: {email}")
        raise HTTPException(404, "User not found")

    number = req.number.strip()
    if not number.startswith("+"):
        raise HTTPException(400, "Phone number must be in E.164 format (e.g. +9198...)")

    whatsapp_to = f"whatsapp:{number}"
    code = make_verification_code()
    crud.set_whatsapp_verification(db, user, code, expires_in_minutes=10)

    try:
        send_whatsapp_message(whatsapp_to, f"Your ProjectAria.PA verification code: {code}")
        logger.info(f"Sent verification code to {number} for user {email}")
    except Exception as e:
        logger.exception(f"Twilio send error for {email}: {e}")
        raise HTTPException(500, f"Twilio send error: {str(e)}")

    return {"status": "sent"}


# -----------------------------
# ✅ Verify WhatsApp Number
# -----------------------------
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
    user_context.set(email)
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")

    if user.whatsapp_verify_code != req.code:
        logger.warning(f"Invalid WhatsApp verification code for {email}")
        raise HTTPException(400, "Invalid verification code")

    if user.whatsapp_verify_expires and user.whatsapp_verify_expires < datetime.utcnow():
        logger.warning(f"Expired WhatsApp code for {email}")
        raise HTTPException(400, "Verification code expired")

    user.whatsapp_no = req.number.strip()
    user.whatsapp_verified = True
    user.whatsapp_verify_code = None
    user.whatsapp_verify_expires = None
    db.commit()

    logger.info(f"WhatsApp verified successfully for {email}")
    return {"status": "verified"}


# -----------------------------
# 💬 Incoming WhatsApp Webhook
# -----------------------------
@router.post("/webhook")
async def whatsapp_webhook(request: Request, x_twilio_signature: str = Header(None), db: Session = Depends(get_db)):
    """Twilio webhook for incoming WhatsApp messages."""
    form_data = await request.form()
    params = dict(form_data)
    signature = x_twilio_signature
    from_number = params.get("From", "")
    body = params.get("Body", "").strip()

    # 🔒 Validate authenticity using actual incoming URL
    url = str(request.url)
    if not validate_twilio_signature(url, params, signature):
        logger.warning("⚠️ Invalid Twilio signature received")
        raise HTTPException(403, "Invalid Twilio signature")

    logger.info(f"Incoming WhatsApp from {from_number}: {body}")
    incoming = from_number.replace("whatsapp:", "").strip()
    user = crud.get_user_by_whatsapp_no(db, incoming)

    if not user:
        logger.warning(f"Unrecognized WhatsApp number: {incoming}")
        send_whatsapp_message(
            from_number,
            "👋 Hi! To link your WhatsApp with ProjectAria.PA, open the web app and connect your number in *Integration → Connect WhatsApp*.",
        )
        return {"status": "unlinked"}

    user_context.set(user.email)

    # --- Simple command recognition ---
    lower = body.lower()
    if "calendar" in lower:
        logger.info(f"User {user.email} requested calendar via WhatsApp")
        events, message = await fetch_today_events_for_user(user)
        if events is None:
            send_whatsapp_message(from_number, f"❌ I couldn’t access your calendar: {message}")
            logger.error(f"Calendar fetch failed for {user.email}: {message}")
        elif not events:
            send_whatsapp_message(from_number, "📭 You have no events in the next 24 hours.")
            logger.info(f"No events for {user.email}")
        else:
            send_whatsapp_message(from_number, "📅 Here are your upcoming events:\n\n" + message)
            logger.info(f"Sent {len(events)} events to {user.email}")
        return {"status": "ok"}

    # Default fallback
    send_whatsapp_message(from_number, "🤖 Hello! Commands available: 'calendar' → today's events.")
    logger.info(f"Replied with default help message to {user.email}")
    return {"status": "ok"}


# -----------------------------
# 🔓 Unlink WhatsApp Number
# -----------------------------
@router.post("/unlink")
async def unlink_whatsapp(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Disconnect a linked WhatsApp number."""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        raise HTTPException(401, "Invalid token")

    email = data.get("sub")
    user_context.set(email)
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")

    user.whatsapp_no = None
    user.whatsapp_verified = False
    db.commit()

    logger.info(f"Unlinked WhatsApp number for {email}")
    return {"status": "unlinked"}
