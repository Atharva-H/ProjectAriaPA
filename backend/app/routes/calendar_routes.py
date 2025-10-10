# app/routes/calendar_routes.py
from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import httpx, os, jwt

from app.db.database import SessionLocal
from app.db.models import User

router = APIRouter(prefix="/calendar", tags=["Calendar"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper to decode JWT
def decode_token(token: str):
    try:
        return jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"], options={"verify_exp": False})
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

# Utility for making authorized Google API calls
async def google_calendar_get(access_token, endpoint, params=None):
    base = "https://www.googleapis.com/calendar/v3/"
    url = base + endpoint
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {access_token}"}, params=params)
        if r.status_code != 200:
            print("❌ Google Calendar API error:", r.text)
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()

# 🗓️ Fetch today's events
@router.get("/today")
async def get_today_events(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user or not user.access_token:
        raise HTTPException(404, "User not found or not linked with Google")

    now_utc = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    start_of_day = (now_utc + ist_offset).replace(hour=0, minute=0, second=0, microsecond=0) - ist_offset
    end_of_day = start_of_day + timedelta(days=1)

    params = {
        "timeMin": start_of_day.isoformat(),
        "timeMax": end_of_day.isoformat(),
        "singleEvents": True,
        "orderBy": "startTime"
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

    return {"events": events, "count": len(events)}


# 🕐 Fetch upcoming events (next N days)
@router.get("/upcoming")
async def get_upcoming_events(days: int = 7, authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(404, "User not found")

    now_utc = datetime.now(timezone.utc)
    timeMin = now_utc.isoformat()
    timeMax = (now_utc + timedelta(days=days)).isoformat()

    params = {
        "timeMin": timeMin,
        "timeMax": timeMax,
        "singleEvents": True,
        "orderBy": "startTime"
    }

    data = await google_calendar_get(user.access_token, "calendars/primary/events", params)
    return {"events": data.get("items", []), "count": len(data.get("items", []))}


# 🔍 Fetch event details by ID
@router.get("/event/{event_id}")
async def get_event_details(event_id: str, authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(404, "User not found")

    data = await google_calendar_get(user.access_token, f"calendars/primary/events/{event_id}")
    return data

