from fastapi import APIRouter, Depends, Header, HTTPException, Request
import logging
from sqlalchemy.orm import Session
from app.db import get_db, crud
from app.core.logging_config import user_context
from app.services.twilio_service import send_whatsapp_message, validate_twilio_signature

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

    user_context.set(user.email)

    # Process message through centralized chat handler
    from app.services.chat_handler import process_message
    
    # We don't need a callback for WhatsApp since we send the response synchronously/immediately after
    result = await process_message(user.id, body, db)
    
    if result.get("status") == "success" and result.get("content"):
        # Send response back to WhatsApp
        send_whatsapp_message(from_number, result["content"])
        return {"status": "success"}
    else:
        # Fallback error message
        reply = "❌ Sorry, I encountered an error processing your request."
        send_whatsapp_message(from_number, reply)
        return {"status": "error"}
