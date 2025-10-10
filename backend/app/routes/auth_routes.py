import httpx
from fastapi import APIRouter, Depends, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db import get_db
from app.db import crud
from app.core.config import settings
from app.core.security import create_jwt, decode_jwt
from app.services.calendar_service import fetch_today_events_for_user

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- Step 1: Start OAuth login ---
@router.get("/login")
async def login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&access_type=offline"
        "&prompt=consent"
        "&scope="
        "openid%20email%20profile%20"
        "https://www.googleapis.com/auth/calendar"
    )
    return RedirectResponse(google_auth_url)


# --- Step 2: Handle OAuth callback ---
@router.get("/callback")
async def callback(code: str, db: Session = Depends(get_db)):
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

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_info_resp.json()

    if not user_info.get("email"):
        return {"error": "Google login failed"}

    expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
    user = crud.get_user_by_google_id(db, user_info["id"])

    if not user:
        user = crud.create_user(
            db,
            google_id=user_info["id"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info["picture"],
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry_time
        )
    else:
        crud.update_user_tokens(db, user, access_token, refresh_token or user.refresh_token, expires_in)

    jwt_token = create_jwt(user.email)
    redirect_url = f"{settings.FRONTEND_URL}/dashboard?token={jwt_token}"
    return RedirectResponse(url=redirect_url, status_code=302)


# --- Step 3: Get current user info ---
@router.get("/me")
async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        return {"error": "Missing Authorization header"}

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        return {"error": "Invalid or expired token"}

    email = data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        return {"error": "User not found"}

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
        return {"error": "Missing Authorization header"}

    old_token = authorization.replace("Bearer ", "")
    data = decode_jwt(old_token)
    if not data:
        return {"error": "Invalid token"}

    email = data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        return {"error": "User not found"}

    # Refresh Google access token if expired
    if datetime.utcnow() > user.token_expiry:
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
    return {"token": new_jwt}
