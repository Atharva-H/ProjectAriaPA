# app/services/gemini_adapter.py
import os
import json
import logging
import google.generativeai as genai
from typing import Dict, Any

from app.services.ai_functions import FUNCTIONS  # ✅ shared function list
from app.utils.helpers import get_logger

logger = get_logger("ProjectAria.Gemini")

# Configure Gemini client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Build a readable function list for prompt context
def format_functions_for_prompt() -> str:
    lines = ["You have access to these backend functions:"]
    for f in FUNCTIONS:
        lines.append(f"- {f['name']}: {f['description']}")
    return "\n".join(lines)


# Base system prompt
PROMPT = f"""
You are ProjectAria's assistant — a smart backend interpreter that reads natural language
and maps it to structured backend function calls.

Respond with ONLY a single valid JSON object:
{{
  "intent": "<function_name or 'unknown'>",
  "params": {{ ... }}
}}

Do not add explanations, markdown, or text outside JSON.
If the user's request does not clearly match any function, use:
{{ "intent": "unknown", "params": {{}} }}

{format_functions_for_prompt()}
"""


async def interpret_message_gemini(message: str) -> Dict[str, Any]:
    """
    Uses Gemini Pro to interpret user message and map to backend function intents.
    Returns standardized JSON: {"intent": str, "params": dict}
    """
    try:
        logger.info(f"🧠 Interpreting message via Gemini: {message}")

        model = genai.GenerativeModel("gemini-pro")
        prompt = PROMPT + f"\nUser: {message}"

        # Gemini generate call
        result = model.generate_content(prompt)
        text_output = (result.text or "").strip()

        # Clean logs
        logger.info(f"📨 Gemini raw output: {text_output[:300]}...")

        # Try to parse JSON safely
        try:
            parsed = json.loads(text_output)
            if isinstance(parsed, dict) and "intent" in parsed:
                logger.info(f"🧩 Gemini chose: {parsed}")
                return parsed
            else:
                logger.warning(f"⚠️ Gemini output not a valid intent dict: {parsed}")
                return {"intent": "unknown", "params": {}}
        except json.JSONDecodeError:
            # Try extracting JSON substring if model added text
            import re
            match = re.search(r"\{.*\}", text_output, re.DOTALL)
            if match:
                try:
                    cleaned = json.loads(match.group(0))
                    logger.info(f"🧩 Gemini recovered JSON: {cleaned}")
                    return cleaned
                except Exception:
                    pass
            logger.warning(f"⚠️ Gemini returned non-JSON: {text_output}")
            return {"intent": "unknown", "params": {}}

    except Exception as e:
        logger.exception(f"Gemini interpretation error: {e}")
        return {"intent": "unknown", "params": {}}
