from fastapi import APIRouter, Depends, Header, HTTPException, Request
import logging
from sqlalchemy.orm import Session
from app.db import get_db, crud
from app.core.logging_config import user_context
from app.services.twilio_service import send_whatsapp_message, validate_twilio_signature
from app.services.ai_service import interpret_message
from app.services.conversation_manager import add_user_message, add_assistant_message, get_recent_chat

# Handlers
from app.routes.whatsapp.handlers import calendar_handler, profile_handler, help_handler, tally_handler

router = APIRouter()
logger = logging.getLogger("ProjectAria.WhatsApp")


@router.post("/webhook")
async def whatsapp_webhook(request: Request, x_twilio_signature: str = Header(None), db: Session = Depends(get_db)):
    """Twilio webhook for incoming WhatsApp messages."""
    form_data = await request.form()
    params = dict(form_data)
    signature = x_twilio_signature
    from_number = params.get("From", "")
    body = params.get("Body", "").strip()

    url = str(request.url)
    if not validate_twilio_signature(url, params, signature):
        raise HTTPException(403, "Invalid Twilio signature")

    incoming = from_number.replace("whatsapp:", "").strip()
    user = crud.get_user_by_whatsapp_no(db, incoming)
    if not user:
        send_whatsapp_message(from_number, "👋 Please link your WhatsApp via ProjectAria.PA dashboard.")
        return {"status": "unlinked"}

    user_context.set(user.email)

    # AI interpretation with short-term memory
    add_user_message(user.id, body)
    history = get_recent_chat(user.id)
    ai_result = await interpret_message(body, history)
    intent = ai_result.get("intent", "unknown")
    params = ai_result.get("params", {})

    # Handle Tally intents
    if intent.startswith("get_tally_"):
        return await tally_handler.handle_tally_intent(intent, params, user, from_number, db)

    elif intent.startswith("get_") or intent.startswith("create_"):
        return await calendar_handler.handle_calendar_intent(intent, params, user, from_number, db)

    elif intent == "get_user_profile":
        return await profile_handler.handle_profile_intent(user, from_number)

    elif intent == "get_help":
        return await help_handler.handle_help_intent(from_number)

    else:
        reply = "🤖 Sorry, I didn't understand that. Try 'Show my meetings today' or 'outstanding of ABC Company'."
        send_whatsapp_message(from_number, reply)
        add_assistant_message(user.id, reply)
        return {"status": "unknown_intent"}
