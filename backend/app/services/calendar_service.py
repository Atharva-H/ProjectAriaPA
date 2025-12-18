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
from datetime import datetime
import pytz
from typing import Tuple, List, Dict

def format_datetime_ist(iso_str: str) -> datetime:
    """Convert ISO datetime string to a datetime object in IST."""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    ist = pytz.timezone("Asia/Kolkata")
    return dt.astimezone(ist)

def humanize_datetime_range(start_iso: str, end_iso: str) -> str:
    """Return clean time range for WhatsApp — hides redundant date, shows (+1) if crosses midnight."""
    start_dt = format_datetime_ist(start_iso)
    end_dt = format_datetime_ist(end_iso)

    # Date parts
    start_day = start_dt.strftime("%a, %d %b")
    end_day = end_dt.strftime("%a, %d %b")
    day_diff = (end_dt.date() - start_dt.date()).days

    # If same day — show short
    if day_diff == 0:
        return f"{start_day} {start_dt.strftime('%I:%M %p')} → {end_dt.strftime('%I:%M %p')}"
    # If crosses to next day
    elif day_diff == 1:
        return f"{start_day} {start_dt.strftime('%I:%M %p')} → {end_dt.strftime('%I:%M %p')} (+1)"
    # If multiple days apart
    else:
        return f"{start_day} {start_dt.strftime('%I:%M %p')} → {end_day} {end_dt.strftime('%I:%M %p')} (+{day_diff})"

def format_event_list(events_data: dict) -> Tuple[List[Dict[str, str]], str]:
    """Format Google Calendar events into a clean, WhatsApp + frontend-friendly structure."""
    events_list = []
    lines = []

    for event in events_data.get("items", []):
        summary = event.get("summary", "No Title")

        # Extract time
        start_iso = event["start"].get("dateTime", event["start"].get("date"))
        end_iso = event["end"].get("dateTime", event["end"].get("date"))

        # Handle all-day events separately
        if "T" not in str(start_iso):
            time_display = f"All-day: {start_iso}"
        else:
            time_display = humanize_datetime_range(start_iso, end_iso)

        # Organizer & attendees
        organizer_name = event.get("organizer", {}).get("displayName")
        organizer_email = event.get("organizer", {}).get("email", "Unknown")
        organizer = organizer_name or organizer_email
        
        # Make email clickable if it's an email address
        if "@" in organizer and organizer == organizer_email:
            organizer = f"[{organizer}](mailto:{organizer})"

        attendees = event.get("attendees", [])
        attendee_names = []
        for a in attendees:
            if not a.get("self"):
                name = a.get("displayName") or a.get("email")
                email = a.get("email")
                # Make email clickable if it's an email address
                if email and "@" in email and name == email:
                    name = f"[{name}](mailto:{name})"
                attendee_names.append(name)
        attendees_str = ", ".join(attendee_names) if attendee_names else "None"

        # Location & meeting link (if available)
        location = event.get("location")
        hangout_link = event.get("hangoutLink")

        # WhatsApp summary (for chat output)
        msg = (
            f"🗓 *{summary}*\n"
            f"⏰ {time_display}\n"
            f"👤 Organizer: {organizer}\n"
            f"👥 Attendees: {attendees_str}"
        )
        if location:
            msg += f"\n📍 Location: {location}"
        if hangout_link:
            msg += f"\n🔗 Link: [{hangout_link}]({hangout_link})"

        # Append for frontend use
        events_list.append({
            "id": event.get("id"),  # used for React keys
            "summary": summary,
            "start": start_iso,
            "end": end_iso,
            "organizer": organizer,
            "attendees": attendee_names,  # list
            "location": location,
            "hangoutLink": hangout_link,
        })
        lines.append(msg)

    if not lines:
        return events_list, "📭 No events found."

    return events_list, "\n\n".join(lines)




# ---------------------------------------------------
# 🔑 Token helper
# ---------------------------------------------------
def _get_calendar_token(user) -> Optional[str]:
    """Prefer the Google Calendar OAuth token; fall back to login token if needed.
    Returns None if no usable token exists.
    """
    if getattr(user, "google_calendar_token", None):
        return user.google_calendar_token
    # Fallback for legacy flows — may have insufficient scopes
    return getattr(user, "access_token", None)


# ---------------------------------------------------
# 🗓️ 1. Fetch today's Google Calendar events
# ---------------------------------------------------
async def fetch_today_events_for_user(user) -> Tuple[Optional[list], str]:
    token = _get_calendar_token(user) if user else None
    if not user or not token:
        logger.warning("Attempted calendar fetch without valid user or calendar token")
        return None, "❌ User or calendar token missing."

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
    token = _get_calendar_token(user) if user else None
    if not user or not token:
        logger.warning("Attempted upcoming fetch without valid user or calendar token")
        return None, "❌ User or calendar token missing."

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
    token = _get_calendar_token(user) if user else None
    if not user or not token:
        return {"error": "❌ User or calendar token missing."}

    user_context.set(user.email)
    logger.info(f"Fetching details for event {event_id} ({user.email})")

    event_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(event_url, headers={"Authorization": f"Bearer {token}"})

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
# 🆕 4. Create new Google Calendar event (with conflict detection)
# ---------------------------------------------------
async def create_event_for_user(
    user,
    title: str,
    description: str = "",
    datetime_str: str = "",
    duration_minutes: int = 60,
    color: str = "default",
    skip_conflict_check: bool = False
) -> dict:
    """
    Creates a new event in the user's Google Calendar.
    Accepts natural language date/time via `dateparser` (e.g. 'tomorrow 2pm').

    - Before creating, checks for conflicts with existing events.
    - If conflict detected, returns structured conflict info.
    """

    token = _get_calendar_token(user) if user else None
    if not user or not token:
        return {"error": "❌ Missing user or calendar token."}

    user_context.set(user.email)
    logger.info(f"Creating calendar event for {user.email}: {title} — {datetime_str}")

    # ---------------------------
    # 🕓 Parse datetime
    # ---------------------------
    # First try to parse as ISO format if it looks like one
    event_start = None
    if "T" in datetime_str and ("+" in datetime_str or "Z" in datetime_str):
        try:
            from dateutil import parser as dateutil_parser
            event_start = dateutil_parser.parse(datetime_str)
            # Convert to IST if not already in a timezone
            if event_start.tzinfo is None:
                event_start = pytz.timezone("Asia/Kolkata").localize(event_start)
            elif "Z" in datetime_str:
                # Convert UTC to IST
                event_start = event_start.astimezone(pytz.timezone("Asia/Kolkata"))
            else:
                # Already has timezone, convert to IST if different
                event_start = event_start.astimezone(pytz.timezone("Asia/Kolkata"))
        except Exception as e:
            logger.warning(f"Failed to parse ISO datetime: {e}")
    
    # If not ISO format, try dateparser for natural language
    if not event_start:
        event_start = dateparser.parse(
            datetime_str,
            settings={
                "TIMEZONE": "Asia/Kolkata",
                "PREFER_DATES_FROM": "future",
                "DATE_ORDER": "DMY",
                "RELATIVE_BASE": datetime.now(pytz.timezone("Asia/Kolkata"))
            }
        )
    
    if not event_start:
        logger.warning(f"Could not parse datetime: {datetime_str}")
        return {"error": f"❌ Could not understand date/time: {datetime_str}"}

    # If parsed time ended up in the past by more than a day, bump year forward
    try:
        now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
        if event_start.tzinfo is None:
            event_start = pytz.timezone("Asia/Kolkata").localize(event_start)
        # if event appears more than 1 day before now, roll year forward to next occurrence
        if (now_ist - event_start).total_seconds() > 24 * 3600:
            event_start = event_start.replace(year=now_ist.year)
            if (now_ist - event_start).total_seconds() > 24 * 3600:
                event_start = event_start.replace(year=now_ist.year + 1)
    except Exception:
        pass

    event_end = event_start + timedelta(minutes=duration_minutes)
    start_utc = event_start.astimezone(timezone.utc)
    end_utc = event_end.astimezone(timezone.utc)

    # ---------------------------
    # ⚖️ Check for conflicts (unless forced to skip)
    # ---------------------------
    if not skip_conflict_check:
        conflicts = await check_conflicts_for_user(user, start_utc, end_utc)
        if conflicts:
            conflict = conflicts[0]
            summary = conflict.get("summary", "Unnamed Event")
            start = conflict["start"].get("dateTime", conflict["start"].get("date"))
            end = conflict["end"].get("dateTime", conflict["end"].get("date"))
            # Format a clear, human-friendly range for WhatsApp
            pretty_range = humanize_datetime_range(str(start), str(end)).replace("→", "-")

            # Get user-specific working hours from database, with fallback to config defaults
            from app.core.config import settings
            work_start_hour = user.working_hours_start if user.working_hours_start is not None else settings.WORK_START_HOUR
            work_end_hour = user.working_hours_end if user.working_hours_end is not None else settings.WORK_END_HOUR
            
            # find best 3–4 free slots within working hours for next 7 days
            free_slots_result = await find_best_free_slots(
                user,
                days=7,
                min_duration_minutes=duration_minutes,
                work_start_hour=work_start_hour,
                work_end_hour=work_end_hour,
            )
            # Handle both old (list of strings) and new (dict with formatted/raw) return formats
            if isinstance(free_slots_result, dict):
                free_slots_formatted = free_slots_result.get("formatted", [])
                free_slots_raw = free_slots_result.get("raw", [])
            else:
                # Legacy format - just strings
                free_slots_formatted = free_slots_result
                free_slots_raw = []
            
            free_str = (
                "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(free_slots_formatted)])
                if free_slots_formatted else "No free slots found."
            )

            message = (
                f"⚠️ Your calendar is booked with '{summary}'\n"
                f"{pretty_range}.\n\n"
                f"Here are available slots between {settings.WORK_START_HOUR} AM and {settings.WORK_END_HOUR} PM for the next 7 days:\n{free_str}\n\n"
                "Reply with the option number or suggest a custom time (e.g., 'Thursday 2:30pm')."
            )

            logger.warning(f"Conflict detected for {user.email}: {summary} ({start}-{end})")
            return {
                "status": "conflict",
                "existing_event": {"id": conflict.get("id"), "summary": summary},
                "message": message,
            }

    # ---------------------------
    # 📅 Create event (no conflict)
    # ---------------------------
    # Map color names to Google Calendar color IDs
    # 1=Lavender, 2=Sage, 3=Grape, 4=Flamingo, 5=Banana, 6=Tangerine, 7=Peacock, 8=Graphite, 9=Blueberry, 10=Basil, 11=Tomato
    # 9=Blue (work), 10=Green (personal)
    color_map = {
        "work": "9",      # Blue
        "personal": "10",  # Green
        "default": None
    }
    
    payload = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_utc.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_utc.isoformat(), "timeZone": "Asia/Kolkata"},
    }
    
    # Add color if specified
    if color in color_map and color_map[color]:
        payload["colorId"] = color_map[color]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code not in (200, 201):
            error_detail = response.json().get("error", {}).get("message", response.text)
            logger.error(
                f"Calendar event creation failed ({response.status_code}): {error_detail}"
            )
            return {"error": error_detail}

        data = response.json()
        logger.info(f"✅ Created event '{data.get('summary')}' for {user.email}")
        
        # Parse start and end times
        start_dt = isoparse(data["start"]["dateTime"])
        end_dt = isoparse(data["end"]["dateTime"])
        
        return {
            "status": "success",
            "event_id": data.get("id"),
            "event_link": data.get("htmlLink"),
            "summary": data.get("summary", title),
            "start": start_dt.isoformat(),  # Convert to ISO string
            "end": end_dt.isoformat(),  # Convert to ISO string
            "description": data.get("description"),
            "location": data.get("location"),
            "organizer": data.get("organizer", {}).get("displayName") or data.get("organizer", {}).get("email"),
            "attendees": [a.get("displayName") or a.get("email") for a in data.get("attendees", [])],
            "hangoutLink": data.get("hangoutLink"),
        }

    except Exception as e:
        logger.exception(f"Error creating event for {user.email}: {e}")
        return {"error": str(e)}


# ---------------------------------------------------
# ⚖️ 5. Check for conflicting events before creating new one
# ---------------------------------------------------
async def check_conflicts_for_user(
    user,
    start_time: datetime,
    end_time: datetime
) -> List[Dict[str, Any]]:
    """
    Returns a list of overlapping events during the given time range.
    """

    token = _get_calendar_token(user) if user else None
    if not user or not token:
        return []

    user_context.set(user.email)
    logger.info(f"Checking for calendar conflicts for {user.email}")

    params = {
        "timeMin": start_time.isoformat(),
        "timeMax": end_time.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?{urlencode(params)}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers={"Authorization": f"Bearer {token}"})

        if res.status_code != 200:
            logger.error(f"Calendar API error {res.status_code}: {res.text}")
            return []

        events = res.json().get("items", [])
        overlapping_events = []

        for e in events:
            existing_start = isoparse(e["start"].get("dateTime", e["start"].get("date")))
            existing_end = isoparse(e["end"].get("dateTime", e["end"].get("date")))
            # Overlap check
            if (existing_start < end_time) and (existing_end > start_time):
                overlapping_events.append(e)

        logger.info(f"Found {len(overlapping_events)} overlapping events for {user.email}")
        return overlapping_events

    except Exception as e:
        logger.exception(f"Error checking conflicts: {e}")
        return []


# ---------------------------------------------------
# 🔧 Internal helper
# ---------------------------------------------------
async def _fetch_and_format_calendar(user, url: str) -> Tuple[Optional[list], str]:
    try:
        token = _get_calendar_token(user) if user else None
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers={"Authorization": f"Bearer {token}"})

        # If 401, try to refresh the token
        if res.status_code == 401 and user and user.google_calendar_refresh:
            logger.info(f"Calendar token expired for {user.email}, attempting refresh...")
            from app.db.crud import refresh_google_access_token
            from app.db import get_db
            from sqlalchemy.orm import Session
            
            token_data = await refresh_google_access_token(user.google_calendar_refresh)
            new_access = token_data.get("access_token")
            if new_access:
                # Update the user's token in DB
                db = next(get_db())
                try:
                    from datetime import datetime, timedelta
                    expiry_time = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
                    from app.db import crud
                    # Fetch fresh user object from the new session
                    fresh_user = crud.get_user_by_email(db, user.email)
                    if fresh_user:
                        crud.update_calendar_tokens(db, fresh_user, new_access, fresh_user.google_calendar_refresh, expiry_time)
                        # Update the original user object with new token
                        user.google_calendar_token = new_access
                        logger.info(f"✅ Calendar token refreshed for {user.email}")
                    else:
                        logger.error(f"Could not find user {user.email} for token update")
                    db.close()
                    
                    # Retry with new token
                    res = await client.get(url, headers={"Authorization": f"Bearer {new_access}"})
                except Exception as e:
                    logger.error(f"Failed to update calendar token: {e}")
                    db.close()

        if res.status_code != 200:
            error_detail = res.json().get("error", {}).get("message", res.text)
            
            # If we tried to refresh and it failed (still 401), tell user to reconnect
            if res.status_code == 401 and user and user.google_calendar_refresh:
                 return None, "⚠️ Your Google Calendar connection has expired. Please go to the Integrations page and reconnect your calendar."

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

async def find_free_slots_for_user(user, days: int = 3, min_gap: int = 30) -> list:
    """
    Returns a list of free time slots (start-end pairs) within the next N days.
    """
    now = datetime.now(timezone.utc)
    time_max = now + timedelta(days=days)

    url = "https://www.googleapis.com/calendar/v3/freeBusy"
    body = {
        "timeMin": now.isoformat(),
        "timeMax": time_max.isoformat(),
        "timeZone": "Asia/Kolkata",
        "items": [{"id": "primary"}],
    }

    token = _get_calendar_token(user) if user else None
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(
            url, headers={"Authorization": f"Bearer {token}"}, json=body
        )

    if res.status_code != 200:
        return []

    busy_slots = res.json().get("calendars", {}).get("primary", {}).get("busy", [])
    free_slots = []
    current = now
    for b in busy_slots:
        start = isoparse(b["start"])
        if (start - current).total_seconds() / 60 > min_gap:
            free_slots.append((current, start))
        current = isoparse(b["end"])

    return free_slots

async def update_event_time(user, event_id: str, new_datetime_str: str, duration_minutes: int = 60, preserve_original_time: bool = False):
    """
    Reschedules an existing event to a new datetime (natural language supported).
    Handles "same time" by preserving the original event's time and applying it to the new date.
    
    Args:
        user: User object
        event_id: Event ID to reschedule
        new_datetime_str: New datetime in natural language or ISO format
        duration_minutes: Duration of the event (default 60)
        preserve_original_time: If True, preserve the original event's time on the new date
    """
    token = _get_calendar_token(user) if user else None
    if not user or not token:
        return {"error": "❌ User or calendar token missing."}
    
    user_context.set(user.email)
    logger.info(f"Rescheduling event {event_id} for {user.email} to {new_datetime_str}")
    
    # Check if "same time" is mentioned in the original string
    new_datetime_lower = new_datetime_str.lower()
    preserve_time = preserve_original_time or "same time" in new_datetime_lower or ("same" in new_datetime_lower and "time" in new_datetime_lower)
    
    # Always fetch original event when "same time" is mentioned or if we need duration
    original_event_time = None
    original_duration_minutes = duration_minutes
    if preserve_time:
        try:
            original_event = await fetch_event_details_for_user(user, event_id)
            if "error" not in original_event:
                start_str = original_event.get("start", {}).get("dateTime") or original_event.get("start", {}).get("date")
                end_str = original_event.get("end", {}).get("dateTime") or original_event.get("end", {}).get("date")
                
                if start_str and "T" in str(start_str):
                    # Has time component, parse it
                    original_start = format_datetime_ist(start_str)
                    original_event_time = original_start.time()
                    
                    # Calculate original duration if not provided
                    if end_str and "T" in str(end_str):
                        original_end = format_datetime_ist(end_str)
                        original_duration_minutes = int((original_end - original_start).total_seconds() / 60)
                        duration_minutes = original_duration_minutes  # Use original duration
        except Exception as e:
            logger.warning(f"Could not fetch original event for 'same time': {e}")
            preserve_time = False
    
    # Try to parse as ISO datetime first (if AI provided it)
    event_start = None
    try:
        # Check if it's an ISO format datetime string
        if "T" in new_datetime_str and ("+" in new_datetime_str or "Z" in new_datetime_str or len(new_datetime_str) > 10):
            # Parse ISO datetime
            if new_datetime_str.endswith("Z"):
                event_start = datetime.fromisoformat(new_datetime_str.replace("Z", "+00:00"))
            else:
                event_start = datetime.fromisoformat(new_datetime_str)
            
            # Convert to IST timezone
            if event_start.tzinfo is None:
                event_start = pytz.timezone("Asia/Kolkata").localize(event_start)
            else:
                event_start = event_start.astimezone(pytz.timezone("Asia/Kolkata"))
            
            logger.info(f"Parsed ISO datetime: {event_start}")
    except (ValueError, AttributeError) as e:
        logger.debug(f"Not an ISO format, trying natural language parser: {e}")
    
    # If ISO parsing failed, try natural language parsing
    if not event_start:
        # Parse the new date (remove "same time" from the string for dateparser)
        date_str_for_parsing = new_datetime_str.replace("same time", "").replace("same", "").strip()
        if not date_str_for_parsing:
            date_str_for_parsing = "tomorrow"  # Default if only "same time" was specified
        
        event_start = dateparser.parse(
            date_str_for_parsing,
            settings={
                "TIMEZONE": "Asia/Kolkata",
                "PREFER_DATES_FROM": "future",
                "DATE_ORDER": "DMY",
                "RELATIVE_BASE": datetime.now(pytz.timezone("Asia/Kolkata"))
            }
        )
        
        try:
            now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
            if event_start and event_start.tzinfo is None:
                event_start = pytz.timezone("Asia/Kolkata").localize(event_start)
            if event_start and (now_ist - event_start).total_seconds() > 24 * 3600:
                event_start = event_start.replace(year=now_ist.year)
                if (now_ist - event_start).total_seconds() > 24 * 3600:
                    event_start = event_start.replace(year=now_ist.year + 1)
        except Exception:
            pass
    
    if not event_start:
        return {"error": f"Could not parse new time: {new_datetime_str}"}
    
    # If "same time" was mentioned, apply the original event's time to the new date
    if preserve_time and original_event_time:
        event_start = event_start.replace(
            hour=original_event_time.hour,
            minute=original_event_time.minute,
            second=original_event_time.second,
            microsecond=original_event_time.microsecond
        )
        logger.info(f"Preserving original time: {original_event_time} on new date: {event_start}")

    event_end = event_start + timedelta(minutes=duration_minutes)
    payload = {
        "start": {"dateTime": event_start.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": event_end.isoformat(), "timeZone": "Asia/Kolkata"},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
            res = await client.patch(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if res.status_code in (200, 201):
            data = res.json()
            logger.info(f"✅ Rescheduled event '{data.get('summary')}' for {user.email}")
            return {"status": "success", "summary": data.get("summary", ""), "start": event_start}
        else:
            error_detail = res.json().get("error", {}).get("message", res.text)
            logger.error(f"Failed to reschedule event: {error_detail}")
            return {"error": error_detail}
    except Exception as e:
        logger.exception(f"Error rescheduling event: {e}")
        return {"error": str(e)}

# ---------------------------------------------------
# 🕓 6. Find best available free slots (next N days)
# ---------------------------------------------------
async def find_best_free_slots(
    user,
    days: int = 7,
    min_duration_minutes: int = 30,
    work_start_hour: int = None,
    work_end_hour: int = None,
    start_date: datetime.date = None,
) -> dict:
    """
    Uses Google Calendar FreeBusy API to find ALL available free slots
    within the user's working hours for the next N days.
    
    Respects user's working hours and working days configuration.
    Returns all slots, not just a limited set.
    """
    # Use user-specific values, then config defaults if not specified
    from app.core.config import settings
    if work_start_hour is None:
        work_start_hour = user.working_hours_start if user and user.working_hours_start is not None else settings.WORK_START_HOUR
    if work_end_hour is None:
        work_end_hour = user.working_hours_end if user and user.working_hours_end is not None else settings.WORK_END_HOUR
    
    # Get working days (default to weekdays if not set)
    import json
    working_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    if user and user.working_days:
        try:
            if isinstance(user.working_days, str):
                working_days = json.loads(user.working_days)
            else:
                working_days = user.working_days
        except:
            pass
    
    token = _get_calendar_token(user) if user else None
    if not user or not token:
        return {"formatted": [], "raw": []}

    user_context.set(user.email)
    logger.info(f"Finding free slots for {user.email} (next {days} days, {work_start_hour}:00-{work_end_hour}:00 IST, days: {working_days})")

    # Convert to IST for working hours calculation
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist)
    
    # If start_date is provided, start from that date instead of now
    if start_date:
        start_dt_ist = ist.localize(datetime.combine(start_date, datetime.min.time()))
        # If start_date is today, don't start before now
        if start_date == now_ist.date():
            start_dt_ist = max(start_dt_ist, now_ist)
        current_start = start_dt_ist
        current_start_utc = current_start.astimezone(timezone.utc)
    else:
        current_start = now_ist
        current_start_utc = now_ist.astimezone(timezone.utc)
    
    end_ist = current_start + timedelta(days=days)
    end_utc = end_ist.astimezone(timezone.utc)

    body = {
        "timeMin": current_start_utc.isoformat(),
        "timeMax": end_utc.isoformat(),
        "timeZone": "Asia/Kolkata",
        "items": [{"id": "primary"}],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                "https://www.googleapis.com/calendar/v3/freeBusy",
                headers={"Authorization": f"Bearer {token}"},
                json=body,
            )

        if res.status_code != 200:
            logger.error(f"FreeBusy API error: {res.text}")
            return {"formatted": [], "raw": []}

        busy_periods = (
            res.json().get("calendars", {}).get("primary", {}).get("busy", [])
        )
        free_slots = []
        
        # Convert busy periods to IST for easier comparison
        busy_ranges = []
        for b in busy_periods:
            start_utc = isoparse(b["start"])
            end_utc = isoparse(b["end"])
            busy_ranges.append((start_utc, end_utc))
        
        # Sort busy periods by start time
        busy_ranges.sort(key=lambda x: x[0])
        
        # Iterate day by day to find free slots within working hours
        current_date = current_start.date() if start_date else now_ist.date()
        end_date = end_ist.date()
        
        while current_date <= end_date:
            current_dt_ist = ist.localize(datetime.combine(current_date, datetime.min.time()))
            day_name = current_dt_ist.strftime("%A")
            
            # Skip if not a working day
            if day_name not in working_days:
                current_date += timedelta(days=1)
                continue
            
            # Set working hours for this day
            work_start_dt_ist = current_dt_ist.replace(hour=work_start_hour, minute=0, second=0)
            work_end_dt_ist = current_dt_ist.replace(hour=work_end_hour, minute=0, second=0)
            
            # Don't start before "now" if it's today
            if current_date == now_ist.date():
                work_start_dt_ist = max(work_start_dt_ist, current_start)
            
            # Convert to UTC for comparison with busy periods
            work_start_utc = work_start_dt_ist.astimezone(timezone.utc)
            work_end_utc = work_end_dt_ist.astimezone(timezone.utc)
            
            # Find all busy periods that overlap with today's working hours
            day_busy_periods = []
            for busy_start_utc, busy_end_utc in busy_ranges:
                # Check if busy period overlaps with today's working hours
                if busy_start_utc < work_end_utc and busy_end_utc > work_start_utc:
                    # Clip busy period to working hours
                    clipped_start = max(busy_start_utc, work_start_utc)
                    clipped_end = min(busy_end_utc, work_end_utc)
                    day_busy_periods.append((clipped_start, clipped_end))
            
            # Sort busy periods for this day
            day_busy_periods.sort(key=lambda x: x[0])
            
            # Find gaps between busy periods
            current_slot_start = work_start_utc
            
            for busy_start_utc, busy_end_utc in day_busy_periods:
                # If there's a gap before this busy period
                if busy_start_utc > current_slot_start:
                    gap_duration = (busy_start_utc - current_slot_start).total_seconds() / 60
                    if gap_duration >= min_duration_minutes:
                        # This is a free slot
                        free_slots.append((current_slot_start, busy_start_utc))
                
                # Move past this busy period
                current_slot_start = max(current_slot_start, busy_end_utc)
            
            # Check if there's free time after the last busy period until end of working hours
            if current_slot_start < work_end_utc:
                gap_duration = (work_end_utc - current_slot_start).total_seconds() / 60
                if gap_duration >= min_duration_minutes:
                    free_slots.append((current_slot_start, work_end_utc))
            
            # Move to next day
            current_date += timedelta(days=1)

        # Format readable slots, but return ALL slots (not just first 4)
        formatted_slots = []
        raw_slots = []
        for s in free_slots:
            start_dt_utc = s[0]
            end_dt_utc = s[1]
            # Convert to IST for display
            start_dt_ist = start_dt_utc.astimezone(ist)
            end_dt_ist = end_dt_utc.astimezone(ist)
            
            # Format for display
            if start_dt_ist.date() == end_dt_ist.date():
                # Same day
                formatted = f"{start_dt_ist.strftime('%A %I:%M %p')} - {end_dt_ist.strftime('%I:%M %p')}"
            else:
                # Spans multiple days
                formatted = f"{start_dt_ist.strftime('%A %I:%M %p')} - {end_dt_ist.strftime('%A %I:%M %p')}"
            
            formatted_slots.append(formatted)
            # Store raw datetime info
            raw_slots.append({
                "start": start_dt_utc.isoformat(),
                "end": end_dt_utc.isoformat(),
                "formatted": formatted,
                "duration_minutes": int((end_dt_utc - start_dt_utc).total_seconds() / 60)
            })

        logger.info(
            f"Found {len(formatted_slots)} free slots for {user.email} (showing all slots)"
        )
        return {
            "formatted": formatted_slots,
            "raw": raw_slots
        }

    except Exception as e:
        logger.exception(f"Error fetching free slots: {e}")
        return {"formatted": [], "raw": []}


# ---------------------------------------------------
# 🕓 7. Get next single meeting
# ---------------------------------------------------
async def get_next_single_meeting(user) -> Tuple[Optional[dict], str]:
    """
    Fetch the very next upcoming event from the user's calendar.
    Returns a single event dict and formatted message.
    """
    token = _get_calendar_token(user) if user else None
    if not user or not token:
        logger.warning("Attempted to get next meeting without valid user or calendar token")
        return None, "❌ User or calendar token missing."

    user_context.set(user.email)
    logger.info(f"Fetching next meeting for {user.email}")

    now_utc = datetime.now(timezone.utc)
    params = {
        "timeMin": now_utc.isoformat(),
        "maxResults": "1",
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    query_string = urlencode(params)
    events_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?{query_string}"
    
    try:
        token = _get_calendar_token(user) if user else None
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(events_url, headers={"Authorization": f"Bearer {token}"})

        if res.status_code != 200:
            error_detail = res.json().get("error", {}).get("message", res.text)
            logger.error(f"Google Calendar API error {res.status_code}: {error_detail}")
            return None, f"❌ Calendar API error: {error_detail}"

        events_data = res.json()
        events_list = events_data.get("items", [])
        
        if not events_list:
            logger.info(f"No upcoming meetings for {user.email}")
            return None, "📭 You have no upcoming meetings."
        
        event = events_list[0]
        events_list_formatted, message = format_event_list({"items": [event]})
        
        logger.info(f"Found next meeting for {user.email}: {event.get('summary', 'Unnamed')}")
        return events_list_formatted[0] if events_list_formatted else None, message

    except httpx.RequestError as e:
        logger.exception(f"Network error while fetching next meeting for {user.email}: {e}")
        return None, f"❌ Network error: {e}"

    except Exception as e:
        logger.exception(f"Unexpected error while fetching next meeting for {user.email}: {e}")
        return None, f"❌ Unexpected error: {e}"


# ---------------------------------------------------
# 🕓 8. Get weekly meetings (7 days)
# ---------------------------------------------------
async def get_weekly_schedule(user) -> Tuple[Optional[list], str]:
    """
    Fetch all events for the current week (next 7 days).
    """
    return await fetch_upcoming_events_for_user(user, days=7)


# ---------------------------------------------------
# 🗑️ 9. Cancel/delete calendar event
# ---------------------------------------------------
async def cancel_event_for_user(user, event_id: str) -> dict:
    """
    Cancel/delete a calendar event.
    """
    token = _get_calendar_token(user) if user else None
    if not user or not token:
        return {"error": "❌ User or calendar token missing."}

    user_context.set(user.email)
    logger.info(f"Canceling event {event_id} for {user.email}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.delete(
                f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

        if res.status_code == 204:
            logger.info(f"✅ Cancelled event {event_id} for {user.email}")
            return {"status": "success", "message": "Event cancelled successfully"}
        else:
            error_detail = res.json().get("error", {}).get("message", res.text)
            logger.error(f"Failed to cancel event: {error_detail}")
            return {"error": f"Failed to cancel event: {error_detail}"}

    except Exception as e:
        logger.exception(f"Error cancelling event: {e}")
        return {"error": str(e)}


# ---------------------------------------------------
# 🔍 10. Check availability at specific time
# ---------------------------------------------------
async def check_availability_at_time(user, datetime_str: str, duration_minutes: int = 60) -> dict:
    """
    Check if user is available at a specific time.
    """
    from dateutil.parser import isoparse
    
    # Parse the datetime
    event_start = dateparser.parse(
        datetime_str,
        settings={
            "TIMEZONE": "Asia/Kolkata",
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY",
            "RELATIVE_BASE": datetime.now(pytz.timezone("Asia/Kolkata"))
        }
    )
    
    if not event_start:
        return {"error": f"Could not parse datetime: {datetime_str}"}
    
    # Adjust year if needed
    try:
        now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
        if event_start.tzinfo is None:
            event_start = pytz.timezone("Asia/Kolkata").localize(event_start)
        if (now_ist - event_start).total_seconds() > 24 * 3600:
            event_start = event_start.replace(year=now_ist.year)
    except Exception:
        pass
    
    event_end = event_start + timedelta(minutes=duration_minutes)
    start_utc = event_start.astimezone(timezone.utc)
    end_utc = event_end.astimezone(timezone.utc)

    # Check for conflicts
    conflicts = await check_conflicts_for_user(user, start_utc, end_utc)
    
    # Format the time nicely
    formatted_time = event_start.strftime('%I:%M %p on %A, %d %b %Y')
    
    if conflicts:
        return {
            "available": False,
            "conflict": conflicts[0].get("summary"),
            "time": formatted_time
        }
    
    return {
        "available": True,
        "time": formatted_time
    }
