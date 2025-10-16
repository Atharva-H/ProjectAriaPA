from app.services.twilio_service import send_whatsapp_message
from app.services.calendar_service import create_event_for_user, fetch_today_events_for_user, fetch_upcoming_events_for_user
from app.services.reminder_service import schedule_reminder
from datetime import timedelta, timezone, datetime
import re
import logging

logger = logging.getLogger("ProjectAria.CalendarHandler")


def _is_time_ambiguous(dt_text: str) -> str:
    """
    Returns the matched time string if it appears to be 12-hour time without AM/PM.
    Examples considered ambiguous: "2", "2:30", "11:05", "12:15" (no am/pm).
    Not ambiguous if:
      - Contains am/pm (case-insensitive)
      - 24-hour times like 14:00
    """
    if not dt_text:
        return ""
    if re.search(r"\b(am|pm)\b", dt_text, flags=re.IGNORECASE):
        return ""
    # find hh or hh:mm
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\b", dt_text)
    if not m:
        return ""
    hour = int(m.group(1))
    # 24-hour like 13:.. not ambiguous
    if hour > 12:
        return ""
    # hours 1-12 without am/pm → ambiguous
    return m.group(0)

async def handle_calendar_intent(intent, params, user, from_number, db):
    if intent == "get_today_events":
        events, message = await fetch_today_events_for_user(user)
        if not events:
            send_whatsapp_message(from_number, "📭 You have no events scheduled for today.")
        else:
            send_whatsapp_message(from_number, f"📅 Today's events:\n\n{message}")
        return {"status": "ok"}

    elif intent == "get_upcoming_events":
        days = int(params.get("days", 7))
        events, message = await fetch_upcoming_events_for_user(user, days)
        send_whatsapp_message(from_number, message or "📭 No events in the next 7 days.")
        return {"status": "ok"}

    elif intent == "create_calendar_event":
        title = params.get("title", "Untitled Event")
        description = params.get("description", "")
        datetime_str = params.get("datetime", "")
        duration = int(params.get("duration_minutes", 60))

        # Ask for AM/PM clarification when necessary
        ambiguous = _is_time_ambiguous(datetime_str)
        if ambiguous:
            send_whatsapp_message(
                from_number,
                (
                    f"⏰ I noticed the time '{ambiguous}' doesn't specify AM or PM.\n"
                    "Please reply with AM or PM (e.g., '2:30 PM')."
                ),
            )
            return {"status": "need_time_clarification"}

        result = await create_event_for_user(user, title, description, datetime_str, duration)

        if result.get("status") == "conflict":
            # Directly forward the conflict message with available slots
            send_whatsapp_message(from_number, result["message"])
            return {"status": "conflict"}

        if result.get("status") != "success":
            send_whatsapp_message(from_number, f"❌ {result.get('error', 'Event creation failed.')}")
            return {"status": "error"}

        event_start = result.get("start")
        summary = result.get("summary", title)
        if not event_start:
            send_whatsapp_message(from_number, f"✅ Event '{summary}' created.")
            return {"status": "ok"}

        run_at_utc = event_start.astimezone(timezone.utc) - timedelta(minutes=10)
        now_utc = datetime.now(timezone.utc)

        if run_at_utc > now_utc:
            reminder = schedule_reminder(
                db,
                user,
                result.get("event_id"),
                run_at_utc,
                f"🔔 Reminder: '{summary}' starts at {event_start.strftime('%I:%M %p')} \n📅 Link: {result['event_link']}"
            )
            link_part = f"\n🔗 Link: {result['event_link']}" if result.get("event_link") else ""
            msg = (
                f"✅ Event '{summary}' created!\n"
                f"Starts at {event_start.strftime('%I:%M %p')}\n"
                f"I'll remind you 10 min before." 
                f"{link_part}"
            )
            send_whatsapp_message(from_number, msg)
        else:
            link_part = f"\n🔗 Link: {result['event_link']}" if result.get("event_link") else ""
            send_whatsapp_message(
                from_number,
                f"✅ Event '{summary}' created (too close for reminder).{link_part}"
            )
        return {"status": "ok"}
