# app/routes/whatsapp/handlers/help_handler.py

import logging
from app.services.help_service import get_help_content
from app.services.twilio_service import send_whatsapp_message
from app.core.logging_config import user_context

logger = logging.getLogger("ProjectAria.HelpHandler")

async def handle_help_intent(from_number: str):
    """Handle help requests with dynamic content generation."""
    
    try:
        # Generate dynamic help content
        help_message = get_help_content()
        
        # Send the help message
        send_whatsapp_message(from_number, help_message)
        
        logger.info(f"📋 Sent dynamic help to {from_number}")
        return {"status": "ok", "message": "Help sent successfully"}
        
    except Exception as e:
        logger.error(f"❌ Error sending help: {str(e)}")
        
        # Fallback to basic help
        fallback_message = (
            "🤖 *ProjectAria Assistant*\n\n"
            "I can help you with:\n"
            "📅 Calendar & Meetings\n"
            "📊 Tally Integration\n"
            "📧 Gmail Integration\n"
            "👤 Profile Management\n\n"
            "Just ask me naturally!"
        )
        
        send_whatsapp_message(from_number, fallback_message)
        return {"status": "error", "message": "Fallback help sent"}

async def handle_what_can_you_do_intent(from_number: str):
    """Handle 'what can you do' requests."""
    return await handle_help_intent(from_number)

async def handle_capabilities_intent(from_number: str):
    """Handle capabilities requests."""
    return await handle_help_intent(from_number)