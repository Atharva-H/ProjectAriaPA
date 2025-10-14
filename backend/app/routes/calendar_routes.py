# app/routes/calendar_routes.py

from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import decode_jwt
from app.core.logging_config import user_context
from app.services.calendar_service import (
    fetch_today_events_for_user,
    fetch_upcoming_events_for_user,
    fetch_event_details_for_user,
)

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
# 🔐 Helper: Decode JWT and get user
# ---------------------------------------------------
def get_current_user(authorization: str, db: Session):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    email = payload.get("sub")
    user_context.set(email)
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(404, "User not found")

    return user


# ---------------------------------------------------
# 🗓️ Routes: Thin wrappers around service functions
# ---------------------------------------------------
@router.get("/today")
async def get_today_events(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    events, message = await fetch_today_events_for_user(user)
    return {"events": events, "message": message}


@router.get("/upcoming")
async def get_upcoming_events(days: int = 7, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    events, message = await fetch_upcoming_events_for_user(user, days)
    return {"events": events, "message": message}


@router.get("/event/{event_id}")
async def get_event_details(event_id: str, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    data = await fetch_event_details_for_user(user, event_id)
    return data
