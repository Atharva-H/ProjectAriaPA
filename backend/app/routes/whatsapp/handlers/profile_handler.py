from app.services.twilio_service import send_whatsapp_message

async def handle_profile_intent(user, from_number):
    msg = (
        f"👤 *Profile*\n"
        f"Name: {user.name}\n"
        f"Email: {user.email}\n"
        f"WhatsApp: {user.whatsapp_no or 'Not linked'}"
    )
    send_whatsapp_message(from_number, msg)
    return {"status": "ok"}
