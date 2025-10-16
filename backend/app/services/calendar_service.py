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
        organizer = (
            event.get("organizer", {}).get("displayName")
            or event.get("organizer", {}).get("email", "Unknown")
        )

        attendees = event.get("attendees", [])
        attendee_names = [
            a.get("displayName") or a.get("email")
            for a in attendees if not a.get("self")
        ]
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
            msg += f"\n🔗 Link: {hangout_link}"

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
    duration_minutes: int = 60
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
    # ⚖️ Check for conflicts
    # ---------------------------
    conflicts = await check_conflicts_for_user(user, start_utc, end_utc)
    if conflicts:
        conflict = conflicts[0]
        summary = conflict.get("summary", "Unnamed Event")
        start = conflict["start"].get("dateTime", conflict["start"].get("date"))
        end = conflict["end"].get("dateTime", conflict["end"].get("date"))
        # Format a clear, human-friendly range for WhatsApp
        pretty_range = humanize_datetime_range(str(start), str(end)).replace("→", "-")

        # find best 3–4 free slots between 9 AM and 8 PM for next 7 days
        free_slots = await find_best_free_slots(
            user,
            days=7,
            min_duration_minutes=duration_minutes,
            work_start_hour=9,
            work_end_hour=20,
        )
        free_str = (
            "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(free_slots)])
            if free_slots else "No free slots found."
        )

        message = (
            f"⚠️ Your calendar is booked with '{summary}'\n"
            f"{pretty_range}.\n\n"
            f"Here are available slots between 9 AM and 8 PM for the next 7 days:\n{free_str}\n\n"
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
    payload = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_utc.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_utc.isoformat(), "timeZone": "Asia/Kolkata"},
    }

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
        return {
            "status": "success",
            "event_id": data.get("id"),
            "event_link": data.get("htmlLink"),
            "summary": data.get("summary", title),
            "start": isoparse(data["start"]["dateTime"]),  # datetime object
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

async def update_event_time(user, event_id: str, new_datetime_str: str, duration_minutes: int = 60):
    """
    Reschedules an existing event to a new datetime (natural language supported).
    """
    event_start = dateparser.parse(
        new_datetime_str,
        settings={
            "TIMEZONE": "Asia/Kolkata",
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY",
            "RELATIVE_BASE": datetime.now(pytz.timezone("Asia/Kolkata"))
        }
    )
    try:
        now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
        if event_start.tzinfo is None:
            event_start = pytz.timezone("Asia/Kolkata").localize(event_start)
        if (now_ist - event_start).total_seconds() > 24 * 3600:
            event_start = event_start.replace(year=now_ist.year)
            if (now_ist - event_start).total_seconds() > 24 * 3600:
                event_start = event_start.replace(year=now_ist.year + 1)
    except Exception:
        pass
    if not event_start:
        return {"error": f"Could not parse new time: {new_datetime_str}"}

    event_end = event_start + timedelta(minutes=duration_minutes)
    payload = {
        "start": {"dateTime": event_start.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": event_end.isoformat(), "timeZone": "Asia/Kolkata"},
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
        res = await client.patch(
            url,
            headers={
                "Authorization": f"Bearer {user.access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if res.status_code in (200, 201):
        data = res.json()
        return {"status": "success", "summary": data.get("summary", ""), "start": event_start}
    else:
        return {"error": res.text}

# ---------------------------------------------------
# 🕓 6. Find best available free slots (next N days)
# ---------------------------------------------------
async def find_best_free_slots(
    user,
    days: int = 7,
    min_duration_minutes: int = 30,
    work_start_hour: int = 10,
    work_end_hour: int = 18,
) -> list:
    """
    Uses Google Calendar FreeBusy API to find the best free slots
    within the user's working hours for the next N days.
    """
    token = _get_calendar_token(user) if user else None
    if not user or not token:
        return []

    user_context.set(user.email)
    logger.info(f"Finding free slots for {user.email} (next {days} days)")

    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    body = {
        "timeMin": now.isoformat(),
        "timeMax": end.isoformat(),
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
            return []

        busy_periods = (
            res.json().get("calendars", {}).get("primary", {}).get("busy", [])
        )
        free_slots = []
        current = now

        # Loop through busy periods and find gaps
        for b in busy_periods:
            start = isoparse(b["start"])
            end_busy = isoparse(b["end"])
            # only consider working hours
            work_start = current.replace(hour=work_start_hour, minute=0, second=0)
            work_end = current.replace(hour=work_end_hour, minute=0, second=0)
            # find gap
            if (start - current).total_seconds() / 60 >= min_duration_minutes:
                if current >= work_start and start <= work_end:
                    free_slots.append((current, start))
            current = max(current, end_busy)

        # If still free after last busy block
        if (end - current).total_seconds() / 60 >= min_duration_minutes:
            free_slots.append((current, end))

        # Format readable slots
        formatted = [
            f"{s[0].astimezone().strftime('%A %I:%M %p')} - {s[1].astimezone().strftime('%I:%M %p')}"
            for s in free_slots[:4]
        ]

        logger.info(
            f"Suggested free slots for {user.email}: {', '.join(formatted) or 'None'}"
        )
        return formatted

    except Exception as e:
        logger.exception(f"Error fetching free slots: {e}")
        return []
