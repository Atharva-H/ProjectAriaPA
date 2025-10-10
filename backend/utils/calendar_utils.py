import httpx
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

def format_event_list(events_data):
    """Return both a structured list and a formatted string for WhatsApp."""
    events_list = []
    lines = []

    for event in events_data.get("items", []):
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        summary = event.get("summary", "No Title")
        events_list.append({"summary": summary, "start": start_time})
        lines.append(f"{start_time} — {summary}")

    return events_list, "\n".join(lines) if lines else "No events today."

async def fetch_today_events_for_user(user):
    """Fetch today's calendar events for a given user (returns events_list, message_string)."""
    if not user or not user.access_token:
        return None, "❌ User or access token missing."

    now_utc = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = now_utc + ist_offset

    # Start and end of today in IST
    start_of_day = now_ist.replace(hour=0, minute=0, second=0, microsecond=0) - ist_offset
    end_of_day = (now_ist.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)) - ist_offset

    params = {
        "timeMin": start_of_day.isoformat(),
        "timeMax": end_of_day.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
    }
    query_string = urlencode(params)
    events_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?{query_string}"

    async with httpx.AsyncClient() as client:
        res = await client.get(events_url, headers={"Authorization": f"Bearer {user.access_token}"})
        if res.status_code != 200:
            return None, f"Calendar API error: {res.status_code}"
        events_data = res.json()

    events_list, message = format_event_list(events_data)
    return events_list, message
