# app/services/gpt_adapter.py
import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI
from app.services.ai_functions import FUNCTIONS  # ✅ shared function list
from app.utils.helpers import get_logger

logger = get_logger("ProjectAria.ChatGPT")

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompt for context
SYSTEM_PROMPT = """
You are ProjectAria's assistant.
Understand user messages about meetings, events, or tasks.

When users say things like:
- "Set meeting with production team today at 2pm"
- "Add review session tomorrow at 11"
→ Use the intent `create_calendar_event`.

Return a JSON like:
{"intent": "create_calendar_event", "params": {"title": "...", "datetime": "...", "description": "..."}}
"""


TOOLS = [
    {"type": "function", "function": f}
    for f in FUNCTIONS
]

async def interpret_message_gpt(message: str) -> Dict[str, Any]:
    """
    Uses OpenAI's function-calling (tools) API to interpret the user's natural language query
    and map it to a backend function intent and parameters.
    """
    try:
        logger.info(f"🧠 Interpreting message via ChatGPT: {message}")

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            tools=[
                {
                    "type": "function",
                    "function": f
                } for f in FUNCTIONS
            ],
            tool_choice="auto",
            temperature=0.0,
        )

        choice = completion.choices[0]
        message_obj = choice.message

        # ✅ Tool calling branch (function call)
        if hasattr(message_obj, "tool_calls") and message_obj.tool_calls:
            func = message_obj.tool_calls[0]
            name = func.function.name
            args = json.loads(func.function.arguments or "{}")
            logger.info(f"🧩 AI chose: {name} {args}")
            return {"intent": name, "params": args}

        # ✅ Fallback (no tool call)
        if hasattr(message_obj, "content") and message_obj.content:
            try:
                parsed = json.loads(message_obj.content)
                return parsed
            except json.JSONDecodeError:
                logger.warning(f"⚠️ AI returned non-JSON: {message_obj.content}")
                return {"intent": "unknown", "params": {}}

        # If nothing was returned at all
        return {"intent": "unknown", "params": {}}

    except Exception as e:
        logger.exception(f"ChatGPT interpretation failed: {e}")
        return {"intent": "unknown", "params": {}}
