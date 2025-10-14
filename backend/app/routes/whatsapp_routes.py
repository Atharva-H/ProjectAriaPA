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
from app.services.ai_service import interpret_message


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

    # -----------------------------
    # 🧠 AI Interpretation Layer
    # -----------------------------
    try:
        ai_result = await interpret_message(body)
        intent = ai_result.get("intent", "unknown")
        params = ai_result.get("params", {})
        logger.info(f"🤖 AI intent detected: {intent} | params: {params}")

        # 1️⃣ Handle calendar-related intents
        if intent == "get_today_events":
            events, message = await fetch_today_events_for_user(user)
            if events is None:
                send_whatsapp_message(from_number, f"❌ Couldn't access your calendar: {message}")
            elif not events:
                send_whatsapp_message(from_number, "📭 You have no events scheduled for today.")
            else:
                send_whatsapp_message(from_number, f"📅 Here are today's events:\n\n{message}")
            logger.info(f"✅ Processed {len(events) if events else 0} events for {user.email}")
            return {"status": "ok"}

        elif intent == "get_upcoming_events":
            days = int(params.get("days", 7))
            # You can reuse your existing calendar_service (add a helper if needed)
            from app.services.calendar_service import fetch_upcoming_events_for_user
            events, message = await fetch_upcoming_events_for_user(user, days)
            if not events:
                send_whatsapp_message(from_number, f"📭 No events in the next {days} days.")
            else:
                send_whatsapp_message(from_number, f"📅 Upcoming {days}-day schedule:\n\n{message}")
            logger.info(f"✅ Sent upcoming events to {user.email}")
            return {"status": "ok"}
        
        elif intent == "create_calendar_event":
            from app.services.calendar_service import create_event_for_user
            from app.services.reminder_service import schedule_reminder
            from datetime import timedelta, timezone, datetime

            title = params.get("title", "Untitled Event")
            description = params.get("description", "")
            datetime_str = params.get("datetime", "")
            duration = int(params.get("duration_minutes", 60))

            result = await create_event_for_user(user, title, description, datetime_str, duration)

            # --- Handle errors first ---
            if result.get("status") != "success":
                send_whatsapp_message(from_number, f"❌ {result.get('error', 'Event creation failed.')}")
                logger.error(f"Calendar event creation failed for {user.email}: {result.get('error')}")
                return {"status": "error"}

            # --- Extract event info ---
            event_start = result.get("start")  # should be datetime object returned by create_event_for_user
            summary = result.get("summary", title)

            if not event_start:
                send_whatsapp_message(from_number, f"✅ Event '{summary}' created (no reminder scheduled — missing start time).")
                logger.warning(f"No start time for event '{summary}' ({user.email})")
                return {"status": "ok"}

            # --- Schedule reminder 10 minutes before ---
            run_at_utc = event_start.astimezone(timezone.utc) - timedelta(minutes=10)
            now_utc = datetime.now(timezone.utc)

            if run_at_utc > now_utc:
                reminder = schedule_reminder(
                    db,
                    user,
                    result.get("event_id"),
                    run_at_utc,
                    f"🔔 Reminder: '{summary}' starts at {event_start.strftime('%I:%M %p')}"
                )
                if reminder:
                    send_whatsapp_message(
                        from_number,
                        f"✅ Event '{summary}' created!\n📅 Link: {result['event_link']}\n\nI'll remind you 10 minutes before it starts."
                    )
                    logger.info(f"✅ Event '{summary}' created and reminder scheduled for {user.email}")
                else:
                    send_whatsapp_message(
                        from_number,
                        f"✅ Event '{summary}' created!\n📅 Link: {result['event_link']}\n\n⚠️ Reminder could not be scheduled (missing WhatsApp number)."
                    )
                    logger.warning(f"Reminder scheduling failed for {user.email}")
            else:
                send_whatsapp_message(
                    from_number,
                    f"✅ Event '{summary}' created!\n📅 Link: {result['event_link']}\n\n(Too close to event time for a reminder.)"
                )
                logger.info(f"Event '{summary}' created for {user.email} — too soon for reminder scheduling.")

            return {"status": "ok"}



        elif intent == "get_user_profile":
            msg = (
                f"👤 *Profile*\n"
                f"Name: {user.name}\n"
                f"Email: {user.email}\n"
                f"WhatsApp: {user.whatsapp_no or 'Not linked'}\n"
            )
            send_whatsapp_message(from_number, msg)
            return {"status": "ok"}

        elif intent == "get_help":
            help_msg = (
                "🤖 *ProjectAria Assistant*\n\n"
                "You can ask me things like:\n"
                "- 'What's my day like?'\n"
                "- 'Show meetings next 3 days'\n"
                "- 'My profile'\n\n"
                "I'm always learning new things!"
            )
            send_whatsapp_message(from_number, help_msg)
            return {"status": "ok"}

        else:
            # Default fallback
            send_whatsapp_message(
                from_number,
                "🤖 Sorry, I didn’t understand that. Try asking:\n"
                "'What's my day like?' or 'Show next 5 days events'."
            )
            logger.info(f"Fallback response for {user.email}: unknown intent")
            return {"status": "ok"}

    except Exception as e:
        logger.exception(f"AI interpretation error for {user.email}: {e}")
        send_whatsapp_message(from_number, "⚠️ Sorry, something went wrong while understanding your request.")
        return {"status": "error"}



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
