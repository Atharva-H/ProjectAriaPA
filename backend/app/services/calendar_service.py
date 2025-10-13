# app/services/calendar_service.py

import httpx
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from typing import Tuple, Optional, List, Dict

from app.core.logging_config import user_context

logger = logging.getLogger("ProjectAria.CalendarService")

# ---------------------------------------------------
# 🧹 Utility: Format events for UI or WhatsApp
# ---------------------------------------------------
def format_event_list(events_data: dict) -> Tuple[List[Dict[str, str]], str]:
    """
    Convert Google Calendar API response into a structured list and formatted message string.
    """
    events_list = []
    lines = []

    for event in events_data.get("items", []):
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        summary = event.get("summary", "No Title")
        events_list.append({"summary": summary, "start": start_time})
        lines.append(f"{start_time} — {summary}")

    if not lines:
        return events_list, "No events today."
    return events_list, "\n".join(lines)


# ---------------------------------------------------
# 🗓️ Main: Fetch today's Google Calendar events
# ---------------------------------------------------
async def fetch_today_events_for_user(user) -> Tuple[Optional[list], str]:
    """
    Fetch today's Google Calendar events for a given user.

    Returns:
        (events_list, message)
    """
    if not user or not user.access_token:
        logger.warning("Attempted calendar fetch without valid user or access token")
        return None, "❌ User or access token missing."

    # Attach context for this user
    user_context.set(user.email)
    logger.info(f"Fetching today's events from Google Calendar for {user.email}")

    now_utc = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = now_utc + ist_offset

    # Define today's window in UTC (based on IST)
    start_of_day_utc = now_ist.replace(hour=0, minute=0, second=0, microsecond=0) - ist_offset
    end_of_day_utc = start_of_day_utc + timedelta(days=1)

    params = {
        "timeMin": start_of_day_utc.isoformat(),
        "timeMax": end_of_day_utc.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    query_string = urlencode(params)
    events_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?{query_string}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                events_url,
                headers={"Authorization": f"Bearer {user.access_token}"}
            )

        if res.status_code != 200:
            try:
                error_detail = res.json().get("error", {}).get("message", "")
            except Exception:
                error_detail = res.text or "Unknown error"
            logger.error(f"Google Calendar API error {res.status_code}: {error_detail}")
            return None, f"❌ Calendar API error {res.status_code}: {error_detail}"

        events_data = res.json()
        events_list, message = format_event_list(events_data)

        logger.info(f"Fetched {len(events_list)} events for {user.email}")
        return events_list, message

    except httpx.RequestError as e:
        logger.exception(f"Network error while fetching calendar for {user.email}: {e}")
        return None, f"❌ Network error: {e}"

    except Exception as e:
        logger.exception(f"Unexpected error while fetching calendar for {user.email}: {e}")
        return None, f"❌ Unexpected error: {e}"
