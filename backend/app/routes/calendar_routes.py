# app/routes/calendar_routes.py

from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import httpx
import logging

from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import decode_jwt
from app.core.logging_config import user_context

router = APIRouter(prefix="/calendar", tags=["Calendar"])
logger = logging.getLogger("ProjectAria.Calendar")

# ---------------------------------------------------
# 📦 Database Dependency
# ---------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------
# 🌐 Google Calendar Utility
# ---------------------------------------------------
async def google_calendar_get(access_token, endpoint, params=None):
    base = "https://www.googleapis.com/calendar/v3/"
    url = base + endpoint
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {access_token}"}, params=params)
        if r.status_code != 200:
            logger.error(f"Google Calendar API error: {r.status_code} — {r.text}")
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


# ---------------------------------------------------
# 🧩 Helper — Extract user from Authorization header
# ---------------------------------------------------
def get_current_user(authorization: str, db: Session):
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_jwt(token)

    if not payload:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = payload.get("sub")
    user_context.set(email)
    user = db.query(User).filter(User.email == email).first()

    if not user:
        logger.error(f"User not found in database: {email}")
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ---------------------------------------------------
# 🗓️ Fetch today's events
# ---------------------------------------------------
@router.get("/today")
async def get_today_events(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    logger.info(f"Fetching today's calendar events for {user.email}")

    now_utc = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    start_of_day = (now_utc + ist_offset).replace(hour=0, minute=0, second=0, microsecond=0) - ist_offset
    end_of_day = start_of_day + timedelta(days=1)

    params = {
        "timeMin": start_of_day.isoformat(),
        "timeMax": end_of_day.isoformat(),
        "singleEvents": True,
        "orderBy": "startTime",
    }

    data = await google_calendar_get(user.access_token, "calendars/primary/events", params)

    events = []
    for item in data.get("items", []):
        events.append({
            "id": item.get("id"),
            "summary": item.get("summary"),
            "description": item.get("description"),
            "location": item.get("location"),
            "htmlLink": item.get("htmlLink"),
            "hangoutLink": item.get("hangoutLink"),
            "start": item["start"].get("dateTime", item["start"].get("date")),
            "end": item["end"].get("dateTime", item["end"].get("date")),
            "organizer": item.get("organizer", {}),
            "attendees": item.get("attendees", []),
            "attachments": item.get("attachments", []),
        })

    logger.info(f"Fetched {len(events)} events for today")
    return {"events": events, "count": len(events)}


# ---------------------------------------------------
# 🕐 Fetch upcoming events (next N days)
# ---------------------------------------------------
@router.get("/upcoming")
async def get_upcoming_events(days: int = 7, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    logger.info(f"Fetching upcoming {days} days of events for {user.email}")

    now_utc = datetime.now(timezone.utc)
    timeMin = now_utc.isoformat()
    timeMax = (now_utc + timedelta(days=days)).isoformat()

    params = {
        "timeMin": timeMin,
        "timeMax": timeMax,
        "singleEvents": True,
        "orderBy": "startTime",
    }

    data = await google_calendar_get(user.access_token, "calendars/primary/events", params)
    logger.info(f"Fetched {len(data.get('items', []))} upcoming events")
    return {"events": data.get("items", []), "count": len(data.get("items", []))}


# ---------------------------------------------------
# 🔍 Fetch event details by ID
# ---------------------------------------------------
@router.get("/event/{event_id}")
async def get_event_details(event_id: str, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    logger.info(f"Fetching event details for {event_id} (user: {user.email})")

    data = await google_calendar_get(user.access_token, f"calendars/primary/events/{event_id}")
    logger.info(f"Fetched event '{data.get('summary', 'Unnamed Event')}' for {user.email}")
    return data
