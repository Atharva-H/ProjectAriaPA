# app/services/ai_service.py
import os
import logging
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger("ProjectAria.AI")

# Lazy import to avoid loading both libraries unnecessarily
def _get_provider():
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    return provider

async def interpret_message(message: str) -> Dict[str, Any]:
    """
    Route natural language messages to the configured AI provider.
    Returns: {"intent": str, "params": dict}
    """
    provider = _get_provider()

    if provider == "gemini":
        from app.services.gemini_adapter import interpret_message_gemini
        return await interpret_message_gemini(message)

    elif provider == "openai" or provider == "chatgpt":
        from app.services.gpt_adapter import interpret_message_gpt
        return await interpret_message_gpt(message)

    else:
        logger.warning(f"⚠️ Unknown AI provider: {provider}, defaulting to OpenAI")
        from app.services.gpt_adapter import interpret_message_gpt
        return await interpret_message_gpt(message)
