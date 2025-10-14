import httpx
import logging
from fastapi import APIRouter, Depends, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db import get_db, crud
from app.core.config import settings
from app.core.security import create_jwt, decode_jwt
from app.core.logging_config import user_context  # 👈 to maintain context for all logs
from app.services.calendar_service import fetch_today_events_for_user

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("ProjectAria.Auth")

# --- Step 1: Start OAuth login ---
@router.get("/login")
async def login(email: str = None, db: Session = Depends(get_db)):
    """
    Start Google OAuth flow.
    If user is new → force consent screen.
    If returning user → skip extra consent.
    """
    SCOPES = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.readonly",
    ]
    scope_str = "%20".join(SCOPES)

    # Check if user already exists in DB (skip consent for returning users)
    prompt = "consent"
    if email:
        user = crud.get_user_by_email(db, email)
        if user:
            prompt = "select_account"  # or "none" to skip even account picker

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&access_type=offline"
        f"&prompt={prompt}"
        f"&scope={scope_str}"
    )

    logger.info(f"Redirecting user to Google OAuth (prompt={prompt})")
    return RedirectResponse(google_auth_url)



# --- Step 2: Handle OAuth callback ---
@router.get("/callback")
async def callback(code: str, db: Session = Depends(get_db)):
    logger.info("Google OAuth callback received, exchanging code for token")
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(token_url, data=data)
        token_data = r.json()
        logger.debug(f"Token data received: {list(token_data.keys())}")

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        # Fetch user info
        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_info_resp.json()

    if not user_info.get("email"):
        logger.error("Google login failed - no email in user info")
        return {"error": "Google login failed"}

    # Set context for logs
    user_email = user_info["email"]
    user_context.set(user_email)

    expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
    user = crud.get_user_by_google_id(db, user_info["id"])

    if not user:
        logger.info(f"Creating new user in DB: {user_email}")
        user = crud.create_user(
            db,
            google_id=user_info["id"],
            email=user_email,
            name=user_info["name"],
            picture=user_info["picture"],
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry_time
        )
    else:
        logger.info(f"Updating tokens for existing user: {user_email}")
        crud.update_user_tokens(db, user, access_token, refresh_token or user.refresh_token, expires_in)

    jwt_token = create_jwt(user_email)
    redirect_url = f"{settings.FRONTEND_URL}/dashboard?token={jwt_token}"

    logger.info(f"OAuth success — redirecting {user_email} to dashboard")
    return RedirectResponse(url=redirect_url, status_code=302)


# --- Step 3: Get current user info ---
@router.get("/me")
async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        logger.warning("Missing Authorization header in /auth/me request")
        return {"error": "Missing Authorization header"}

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        logger.warning("Invalid or expired JWT token in /auth/me")
        return {"error": "Invalid or expired token"}

    email = data.get("sub")
    user_context.set(email)
    user = crud.get_user_by_email(db, email)
    if not user:
        logger.error(f"User not found in DB: {email}")
        return {"error": "User not found"}

    logger.info(f"Fetched user info for: {email}")
    return {
        "name": user.name,
        "email": user.email,
        "picture": user.picture,
        "whatsapp_no": user.whatsapp_no,
        "whatsapp_verified": user.whatsapp_verified,
    }


# --- Step 4: Refresh JWT & Google access token ---
@router.get("/refresh")
async def refresh_jwt(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        logger.warning("Missing Authorization header in /auth/refresh")
        return {"error": "Missing Authorization header"}

    old_token = authorization.replace("Bearer ", "")
    data = decode_jwt(old_token)
    if not data:
        logger.warning("Invalid or expired JWT during refresh")
        return {"error": "Invalid token"}

    email = data.get("sub")
    user_context.set(email)
    user = crud.get_user_by_email(db, email)
    if not user:
        logger.error(f"Refresh requested by unknown user: {email}")
        return {"error": "User not found"}

    # Refresh Google access token if expired
    if datetime.utcnow() > user.token_expiry:
        logger.info(f"Refreshing Google access token for: {email}")
        async with httpx.AsyncClient() as client:
            token_data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": user.refresh_token,
                "grant_type": "refresh_token"
            }
            token_resp = await client.post("https://oauth2.googleapis.com/token", data=token_data)
            new_tokens = token_resp.json()
            user.access_token = new_tokens.get("access_token")
            user.token_expiry = datetime.utcnow() + timedelta(seconds=new_tokens.get("expires_in", 3600))
            db.commit()

    new_jwt = create_jwt(user.email)
    logger.info(f"Issued new JWT token for {email}")
    return {"token": new_jwt}
