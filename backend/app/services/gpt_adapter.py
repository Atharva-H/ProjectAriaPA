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
You are ProjectAria's assistant.
Understand user messages about meetings, events, or tasks.

When users say things like:
- "Set meeting with production team today at 2pm"
- "Add review session tomorrow at 11"
→ Use the intent `create_calendar_event`.

Return a JSON like:
{"intent": "create_calendar_event", "params": {"title": "...", "datetime": "...", "description": "..."}}

Rules for datetime extraction:
- Resolve relative phrases to explicit FUTURE times in Asia/Kolkata (IST). Examples: "coming Monday" → next Monday; "this weekend" → next weekend if today is already past; "next Fri"; etc.
- Prefer future dates when ambiguous; if day-only, pick next occurrence.
- Include AM/PM when using 12-hour times; if user omitted AM/PM for 1–12 hour, infer from context or ask for PM for business hours when likely.
- If user gave a follow-up like "tomorrow at 3:30pm" after a conflict about "checking stock", keep the original context/topic in the title or description.
- Output `params.datetime` as a human-entered string that includes clear date and time (e.g., "20 Oct 2025 6:00 PM") or ISO-like ("2025-10-20 18:00").
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
        # include recent conversational context (if any)
        if history:
            for m in history[-8:]:  # cap to last 8 messages
                if m.get("role") in ("user", "assistant") and m.get("content"):
                    chat_messages.append({"role": m["role"], "content": m["content"]})
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
