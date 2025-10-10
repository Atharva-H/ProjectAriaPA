import httpx
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from typing import Tuple, Optional, List, Dict

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


async def fetch_today_events_for_user(user) -> Tuple[Optional[list], str]:
    """
    Fetch today's Google Calendar events for a given user.

    Returns:
        (events_list, message)
    """
    if not user or not user.access_token:
        return None, "❌ User or access token missing."

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

    async with httpx.AsyncClient() as client:
        res = await client.get(
            events_url,
            headers={"Authorization": f"Bearer {user.access_token}"}
        )

        if res.status_code != 200:
            try:
                error_detail = res.json().get("error", {}).get("message", "")
            except Exception:
                error_detail = ""
            return None, f"❌ Calendar API error {res.status_code}: {error_detail or 'Unknown error'}"

        events_data = res.json()

    events_list, message = format_event_list(events_data)
    return events_list, message
