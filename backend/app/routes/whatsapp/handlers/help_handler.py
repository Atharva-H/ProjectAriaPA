from app.services.twilio_service import send_whatsapp_message

async def handle_help_intent(from_number):
    msg = (
        "🤖 *ProjectAria Assistant*\n\n"
        "You can ask me:\n"
        "- 'What's my day like?'\n"
        "- 'Show meetings next 3 days'\n"
        "- 'Create meeting with Rahul tomorrow 3pm'\n"
        "- 'My profile'"
    )
    send_whatsapp_message(from_number, msg)
    return {"status": "ok"}
