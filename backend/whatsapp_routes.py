import os
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request, Header, Depends, HTTPException
from pydantic import BaseModel
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from utils.calendar_utils import fetch_today_events_for_user

from database import SessionLocal
from models import User

load_dotenv()
router = APIRouter(prefix="/whatsapp")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
TWILIO_WEBHOOK_URL = os.getenv("TWILIO_WEBHOOK_URL")  # must match Twilio config

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
validator = RequestValidator(TWILIO_AUTH_TOKEN)

# simple dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helpers ---
def make_verification_code():
    return f"{random.randint(100000, 999999)}"

def send_whatsapp_message(to_whatsapp, body):
    """to_whatsapp: 'whatsapp:+91...'"""
    return client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=to_whatsapp,
        body=body
    )


# --- request schemas ---
class LinkRequest(BaseModel):
    number: str  # e.g. +919876543210

class VerifyRequest(BaseModel):
    number: str
    code: str

# --- Endpoints ---


@router.post("/link")
async def link_whatsapp(req: LinkRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    """Authenticated user asks to link a WhatsApp number.
       We will send a verification code via WhatsApp to that number."""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    import jwt as pyjwt
    JWT_SECRET = os.getenv("JWT_SECRET")


    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"], options={"verify_exp": False})
        email = payload.get("sub")
    except Exception:
        raise HTTPException(401, "Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")

    # normalize number: ensure it doesn't include 'whatsapp:'
    number = req.number.strip()
    if not number.startswith("+"):
        raise HTTPException(400, "Phone number must be in E.164 format, e.g. +9198xxxx")
    whatsapp_to = f"whatsapp:{number}"

    # generate verification
    code = make_verification_code()
    user.whatsapp_verify_code = code
    user.whatsapp_verify_expires = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    # send message via Twilio
    try:
        send_whatsapp_message(whatsapp_to, f"Your ProjectAria.PA verification code: {code}")
    except Exception as e:
        raise HTTPException(500, f"Twilio send error: {str(e)}")

    return {"status": "sent"}


@router.post("/verify")
async def verify_whatsapp(req: VerifyRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    """User posts back the verification code to confirm their number."""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    import jwt as pyjwt
    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"], options={"verify_exp": False})
        email = payload.get("sub")
    except Exception:
        raise HTTPException(401, "Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")

    # same normalization
    number = req.number.strip()
    if user.whatsapp_verify_code != req.code:
        raise HTTPException(400, "Invalid verification code")

    if user.whatsapp_verify_expires and user.whatsapp_verify_expires < datetime.utcnow():
        raise HTTPException(400, "Verification code expired")

    # success -> store number and mark verified
    user.whatsapp_no = number
    user.whatsapp_verified = True
    user.whatsapp_verify_code = None
    user.whatsapp_verify_expires = None
    db.commit()
    return {"status": "verified"}


@router.post("/webhook")
async def whatsapp_webhook(request: Request, x_twilio_signature: str = Header(None), db: Session = Depends(get_db)):
    """Twilio will POST form-encoded data here when a WhatsApp message arrives.
       We verify the request signature and then process the message."""
    # Validate signature (make sure TWILIO_WEBHOOK_URL exactly matches Twilio's configured webhook)
    raw_body = await request.form()
    params = dict(raw_body)  # form params
    url = TWILIO_WEBHOOK_URL
    signature = x_twilio_signature
    if not validator.validate(url, params, signature):
        # signature invalid
        return "Invalid signature", 403

    from_number = params.get("From")  # e.g. "whatsapp:+919876543210"
    body = params.get("Body", "").strip()
    print(f"Incoming whatsapp from {from_number}: {body}")

    # Normalize incoming number
    incoming = from_number.replace("whatsapp:", "").strip()

    # Lookup user by whatsapp_no
    user = db.query(User).filter(User.whatsapp_no == incoming).first()
    if not user:
        # reply asking them to link
        send_whatsapp_message(from_number, "Hi — to link your WhatsApp with ProjectAria.PA please open the web app and connect your number in Integration -> Connect WhatsApp.")
        return "OK"

    # Simple command parsing (extend as needed)
    lower = body.lower()
    if "calendar" in lower:
        # fetch events for user
        events, message = await fetch_today_events_for_user(user)
        if events is None:
            # error during calendar fetch -> send message
            send_whatsapp_message(from_number, f"Sorry, I couldn't access your calendar: {message}")
        elif not events:
            send_whatsapp_message(from_number, "You have no events in the next 24 hours.")
        else:
            # send formatted summary (chunk if long)
            send_whatsapp_message(from_number, "Here are your upcoming events:\n\n" + message)
        return "OK"

    # fallback reply
    send_whatsapp_message(from_number, "Hello! Commands: 'calendar' → today's events. More features coming soon.")
    return "OK"
