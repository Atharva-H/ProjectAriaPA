# app/services/calendar_service.py

import httpx
import logging
from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse

from urllib.parse import urlencode
from typing import Tuple, Optional, List, Dict, Any
import dateparser 
from app.core.logging_config import user_context

logger = logging.getLogger("ProjectAria.CalendarService")

# ---------------------------------------------------
# 🧹 Utility: Format events for UI or WhatsApp
# ---------------------------------------------------
def format_event_list(events_data: dict) -> Tuple[List[Dict[str, str]], str]:
    events_list = []
    lines = []

    for event in events_data.get("items", []):
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        summary = event.get("summary", "No Title")
        events_list.append({"summary": summary, "start": start_time})
        lines.append(f"{start_time} — {summary}")

    if not lines:
        return events_list, "No events found."
    return events_list, "\n".join(lines)


# ---------------------------------------------------
# 🗓️ 1. Fetch today's Google Calendar events
# ---------------------------------------------------
async def fetch_today_events_for_user(user) -> Tuple[Optional[list], str]:
    if not user or not user.access_token:
        logger.warning("Attempted calendar fetch without valid user or access token")
        return None, "❌ User or access token missing."

    user_context.set(user.email)
    logger.info(f"Fetching today's events from Google Calendar for {user.email}")

    now_utc = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = now_utc + ist_offset
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
    return await _fetch_and_format_calendar(user, events_url)


# ---------------------------------------------------
# 🗓️ 2. Fetch upcoming events (next N days)
# ---------------------------------------------------
async def fetch_upcoming_events_for_user(user, days: int = 7) -> Tuple[Optional[list], str]:
    if not user or not user.access_token:
        logger.warning("Attempted upcoming fetch without valid user or access token")
        return None, "❌ User or access token missing."

    user_context.set(user.email)
    logger.info(f"Fetching next {days} days of events for {user.email}")

    now_utc = datetime.now(timezone.utc)
    params = {
        "timeMin": now_utc.isoformat(),
        "timeMax": (now_utc + timedelta(days=days)).isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    query_string = urlencode(params)
    events_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?{query_string}"
    return await _fetch_and_format_calendar(user, events_url)


# ---------------------------------------------------
# 🔍 3. Fetch event details by ID
# ---------------------------------------------------
async def fetch_event_details_for_user(user, event_id: str) -> Dict[str, Any]:
    if not user or not user.access_token:
        return {"error": "❌ User or access token missing."}

    user_context.set(user.email)
    logger.info(f"Fetching details for event {event_id} ({user.email})")

    event_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(event_url, headers={"Authorization": f"Bearer {user.access_token}"})

        if res.status_code != 200:
            error_detail = res.json().get("error", {}).get("message", res.text)
            logger.error(f"Calendar API error {res.status_code}: {error_detail}")
            return {"error": error_detail}

        data = res.json()
        logger.info(f"Fetched event '{data.get('summary', 'Unnamed Event')}' for {user.email}")
        return data

    except Exception as e:
        logger.exception(f"Unexpected error while fetching event {event_id}: {e}")
        return {"error": str(e)}

# ---------------------------------------------------
# 🆕 4. Create new Google Calendar event
# ---------------------------------------------------
async def create_event_for_user(
    user,
    title: str,
    description: str = "",
    datetime_str: str = "",
    duration_minutes: int = 60
) -> dict:
    """
    Creates a new event in the user's Google Calendar.
    Accepts natural language date/time via `dateparser` (e.g. 'tomorrow 2pm').
    """

    if not user or not user.access_token:
        return {"error": "❌ Missing user or access token."}

    user_context.set(user.email)
    logger.info(f"Creating calendar event for {user.email}: {title} — {datetime_str}")

    # Parse datetime
    event_start = dateparser.parse(datetime_str, settings={"TIMEZONE": "Asia/Kolkata"})
    if not event_start:
        logger.warning(f"Could not parse datetime: {datetime_str}")
        return {"error": f"❌ Could not understand date/time: {datetime_str}"}

    # Convert to UTC and calculate end time
    event_end = event_start + timedelta(minutes=duration_minutes)
    start_iso = event_start.astimezone(timezone.utc).isoformat()
    end_iso = event_end.astimezone(timezone.utc).isoformat()

    payload = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_iso, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_iso, "timeZone": "Asia/Kolkata"},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={
                    "Authorization": f"Bearer {user.access_token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

        if response.status_code != 200 and response.status_code != 201:
            error_detail = response.json().get("error", {}).get("message", response.text)
            logger.error(f"Calendar event creation failed ({response.status_code}): {error_detail}")
            return {"error": error_detail}

        data = response.json()
        logger.info(f"✅ Created event '{data.get('summary')}' for {user.email}")
        return {
            "status": "success",
            "event_id": data.get("id"),
            "event_link": data.get("htmlLink"),
            "summary": data.get("summary", title),
            "start": isoparse(data["start"]["dateTime"])  # datetime object
        }

    except Exception as e:
        logger.exception(f"Error creating event for {user.email}: {e}")
        return {"error": str(e)}

# ---------------------------------------------------
# 🔧 Internal helper
# ---------------------------------------------------
async def _fetch_and_format_calendar(user, url: str) -> Tuple[Optional[list], str]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers={"Authorization": f"Bearer {user.access_token}"})

        if res.status_code != 200:
            error_detail = res.json().get("error", {}).get("message", res.text)
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
