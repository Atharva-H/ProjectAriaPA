from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import httpx
import logging

from app.db import crud, get_db
from app.core.config import settings
from app.core.security import decode_jwt
from app.core.logging_config import user_context

router = APIRouter(prefix="/integrations/google/calendar", tags=["Google Calendar"])
logger = logging.getLogger("ProjectAria.GoogleCalendar")

SCOPES = [
    # Identity scopes to fetch user email from userinfo endpoint
    "openid",
    "email",
    "profile",
    # Calendar scopes
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


@router.get("/connect")
async def connect_google_calendar(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    email = payload.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")

    scope_str = " ".join(SCOPES)

    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_CALENDAR_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scope_str}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    logger.info(f"Google Calendar OAuth redirect URI: {google_auth_url}")
    return {"auth_url": google_auth_url}


@router.get("/callback")
async def calendar_callback(code: str, db: Session = Depends(get_db)):
    """Handle OAuth callback for Google Calendar."""
    logger.info("Google Calendar OAuth callback received")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(token_url, data=data)
        token_data = res.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)
    expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)

    # Fetch user info
    async with httpx.AsyncClient() as client:
        user_info = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    info = user_info.json()

    email = info.get("email")
    if not email:
        logger.error(
            "OAuth Calendar: No email in user info — status=%s body=%s",
            getattr(user_info, "status_code", None),
            info
        )
        return {"error": "Failed to fetch Google user info", "details": info}

    user_context.set(email)
    user = crud.get_user_by_email(db, email)
    if not user:
        return {"error": "User not found"}

    crud.update_calendar_tokens(db, user, access_token, refresh_token, expiry_time)
    logger.info(f"✅ Google Calendar connected for {email}")

    redirect_url = f"{settings.FRONTEND_URL}/integration?connected=calendar"
    return RedirectResponse(redirect_url)
