# app/services/gpt_adapter.py
import os
import json
import logging
from typing import Dict, Any, List
from openai import OpenAI
from app.services.ai_functions import FUNCTIONS  # ✅ shared function list
from app.utils.helpers import get_logger

logger = get_logger("ProjectAria.ChatGPT")

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompt for context
SYSTEM_PROMPT = """
You are ProjectAria's assistant for calendar and Tally data.

CRITICAL: ACTION verbs (setup/schedule/book/create) → `create_calendar_event`. QUERY words (what's/show me/am I free) → query functions.

Calendar functions:
- create_calendar_event: For scheduling/booking NEW meetings (Name only in english)
  - Use color="work" for business/work meetings (blue)
  - Use color="personal" for personal appointments (green)
  - Use color="default" when uncertain
- reschedule_calendar_event: For MOVING/CHANGING TIME of existing events (PRIORITY for "reschedule", "move", "change time")
- get_today_events: Today's calendar
- get_next_meeting: VIEW next upcoming event ONLY (read-only, not for rescheduling)
- get_weekly_meetings: This week's schedule
- get_upcoming_events: Next N days
- find_free_time: Check availability
- cancel_calendar_event: Delete events

Tally functions:
- get_tally_ledger_balance: Outstanding/balance queries (PRIORITY for "outstanding"/"balance"/"amount due")
- get_tally_ledger_list, get_tally_vouchers, get_tally_stock_items, get_tally_parties

Capabilities: get_help

Extract datetime as natural language (e.g. "tomorrow 3pm", "Monday 2:30pm"). Resolve to Asia/Kolkata (IST).
Return: {"intent": "function_name", "params": {...}}
"""


TOOLS = [
    {"type": "function", "function": f}
    for f in FUNCTIONS
]

async def interpret_message_gpt(message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Uses OpenAI's function-calling (tools) API to interpret the user's natural language query
    and map it to a backend function intent and parameters.
    """
    try:
        logger.info(f"🧠 Interpreting message via ChatGPT: {message}")

        chat_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        # Provide current date/time context in IST for correct year/day resolution
        try:
            from datetime import datetime
            import pytz
            now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
            chat_messages.append({
                "role": "system",
                "content": f"Current date/time (IST): {now_ist.strftime('%A, %d %b %Y %I:%M %p')}"
            })
        except Exception:
            pass
        # Skip conversation history to avoid confusion from previous messages
        # Each message is interpreted independently for cleaner intent recognition
        chat_messages.append({"role": "user", "content": message})

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_messages,
            tools=[
                {
                    "type": "function",
                    "function": f
                } for f in FUNCTIONS
            ],
            tool_choice="auto",
            temperature=0.0,
            max_tokens=100,
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

        # ✅ Fallback (no tool call) - AI wants to chat directly
        if hasattr(message_obj, "content") and message_obj.content:
            try:
                parsed = json.loads(message_obj.content)
                return parsed
            except json.JSONDecodeError:
                # Not JSON - it's a regular chat message from AI
                logger.info(f"💬 AI wants to chat directly: {message_obj.content}")
                return {"intent": "chat", "content": message_obj.content}

        # If nothing was returned at all
        return {"intent": "unknown", "params": {}}

    except Exception as e:
        # Check if it's a rate limit error
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            logger.error(f"⚠️ OpenAI rate limit reached. Please try again in a few moments.")
            return {
                "intent": "unknown", 
                "params": {},
                "error": "Rate limit exceeded. Please wait a moment and try again."
            }
        
        logger.exception(f"ChatGPT interpretation failed: {e}")
        return {"intent": "unknown", "params": {}, "error": str(e)}
