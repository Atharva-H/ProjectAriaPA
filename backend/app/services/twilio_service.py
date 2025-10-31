# app/services/twilio_service.py

import random
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
from app.core.config import settings
from app.core.logging_config import user_context

logger = logging.getLogger("ProjectAria.Twilio")

# Initialize Twilio client and validator once
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)


# ---------------------------------------------------
# 🔢 Generate verification code
# ---------------------------------------------------
def make_verification_code() -> str:
    """Generate a random 6-digit OTP code."""
    code = f"{random.randint(100000, 999999)}"
    logger.debug(f"Generated verification code: {code[:2]}****")  # partially masked
    return code


# ---------------------------------------------------
# 💬 Send WhatsApp message
# ---------------------------------------------------
def send_whatsapp_message(to_whatsapp: str, body: str):
    """
    Send a WhatsApp message using Twilio API.
    Returns: Twilio message SID or raises HTTPException on failure.
    """
    user_id = user_context.get() or "anonymous"
    logger.info(f"Attempting to send WhatsApp message to {to_whatsapp} (user: {user_id})")

    try:
        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_whatsapp,
            body=body,
        )
        logger.info(f"✅ WhatsApp message sent to {to_whatsapp} (SID: {msg.sid})")
        return msg.sid

    except TwilioRestException as e:
        logger.error(
            f"❌ Twilio API error while sending to {to_whatsapp} (user: {user_id}) — "
            f"Code: {e.code}, Message: {e.msg}"
        )
        
        # Handle rate limiting gracefully
        if e.code == 63038:  # Daily message limit exceeded
            logger.warning(f"⚠️ Twilio rate limit exceeded for {to_whatsapp}. Message not sent.")
            return None  # Return None instead of raising exception
        
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error sending WhatsApp message to {to_whatsapp}: {e}")
        raise e


# ---------------------------------------------------
# 🛡️ Validate Twilio webhook signature
# ---------------------------------------------------
def validate_twilio_signature(url: str, params: dict, signature: str) -> bool:
    """
    Verify that webhook came from Twilio.
    Returns True if valid, False otherwise.
    """
    try:
        valid = validator.validate(url, params, signature)
        if valid:
            logger.info("✅ Valid Twilio webhook signature")
        else:
            logger.warning("⚠️ Invalid Twilio webhook signature")
        return valid
    except Exception as e:
        logger.exception(f"Error while validating Twilio signature: {e}")
        return False
