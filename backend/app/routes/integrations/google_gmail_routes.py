from fastapi import APIRouter, Header, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import httpx
import logging

from app.db import crud, get_db
from app.core.config import settings
from app.core.security import decode_jwt
from app.core.logging_config import user_context

router = APIRouter(prefix="/integrations/google/gmail", tags=["Google Gmail"])
logger = logging.getLogger("ProjectAria.GoogleGmail")

SCOPES = [
    # Identity scopes to fetch user email from userinfo endpoint
    "openid",
    "email",
    "profile",
    # Gmail read-only access
    "https://www.googleapis.com/auth/gmail.readonly"
]


@router.get("/connect")
async def connect_gmail(authorization: str = Header(None)):
    """Start OAuth for Gmail (read-only)."""
    if not authorization:
        return {"error": "Missing Authorization header"}

    token = authorization.replace("Bearer ", "")
    user = decode_jwt(token)
    if not user:
        return {"error": "Invalid token"}

    email = user.get("sub")
    user_context.set(email)
    scope_str = "%20".join(SCOPES)

    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_GMAIL_REDIRECT_URI}"
        "&response_type=code"
        "&access_type=offline"
        "&prompt=consent"
        f"&scope={scope_str}"
    )

    logger.info(f"Redirecting {email} to Gmail OAuth")
    return RedirectResponse(google_auth_url)


@router.get("/callback")
async def gmail_callback(code: str, db: Session = Depends(get_db)):
    """Handle Gmail OAuth callback."""
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_GMAIL_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(token_url, data=data)
        token_data = res.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)
    expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)

    # Fetch Gmail user info
    async with httpx.AsyncClient() as client:
        info_res = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    info = info_res.json()
    email = info.get("email")

    if not email:
        logger.error(
            "OAuth Gmail: No email in user info — status=%s body=%s",
            getattr(info_res, "status_code", None),
            info
        )
        return {"error": "Failed to fetch Gmail user info", "details": info}

    user_context.set(email)
    user = crud.get_user_by_email(db, email)
    if not user:
        return {"error": "User not found"}

    crud.update_gmail_tokens(db, user, access_token, refresh_token, expiry_time)
    logger.info(f"✅ Gmail connected for {email}")

    redirect_url = f"{settings.FRONTEND_URL}/integration?connected=gmail"
    return RedirectResponse(redirect_url)
