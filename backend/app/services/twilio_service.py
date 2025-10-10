import os
import random
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from app.core.config import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)


def make_verification_code():
    return f"{random.randint(100000, 999999)}"


def send_whatsapp_message(to_whatsapp: str, body: str):
    """Send a WhatsApp message using Twilio API."""
    return client.messages.create(
        from_=settings.TWILIO_WHATSAPP_FROM,
        to=to_whatsapp,
        body=body
    )


def validate_twilio_signature(url: str, params: dict, signature: str) -> bool:
    """Verify that webhook came from Twilio."""
    return validator.validate(url, params, signature)
