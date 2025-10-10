import os
import httpx
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from dotenv import load_dotenv
from utils.calendar_utils import fetch_today_events_for_user



load_dotenv()
router = APIRouter(prefix="/auth")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")


# --- Utility ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Step 1: Start OAuth login ---
@router.get("/login")
async def login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&access_type=offline"  # get refresh token too
        "&prompt=consent"       # force consent to update scopes
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
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(token_url, data=data)
        token_data = r.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        # Fetch user info from Google
        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_info_resp.json()

    if not user_info.get("email"):
        return {"error": "Google login failed"}

    # Store or update user in DB
    expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
    user = db.query(User).filter(User.google_id == user_info["id"]).first()

    if not user:
        user = User(
            google_id=user_info["id"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info["picture"],
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry_time,
        )
        db.add(user)
    else:
        user.access_token = access_token
        user.refresh_token = refresh_token or user.refresh_token
        user.token_expiry = expiry_time

    db.commit()
    db.refresh(user)

    # Create JWT valid for 1 hour
    jwt_token = jwt.encode(
        {"sub": user.email, "exp": datetime.utcnow() + timedelta(hours=1)},
        JWT_SECRET,
        algorithm="HS256",
    )

    # Redirect user to frontend dashboard with token
    redirect_url = f"{FRONTEND_URL}/dashboard?token={jwt_token}"
    print(f"✅ Redirecting to: {redirect_url}")  # Debug log
    return RedirectResponse(url=redirect_url, status_code=302)


# --- Step 3: Get current user info ---
@router.get("/me")
async def get_current_user(authorization: str = Header(None)):
    """Return current user's info (based on stored JWT)."""
    import jwt as pyjwt
    if not authorization:
        return {"error": "Missing Authorization header"}

    token = authorization.replace("Bearer ", "")
    try:
        data = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        email = data.get("sub")

        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()

        if not user:
            return {"error": "User not found"}

        # Check if token expired
        exp = data.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            # Token expired → issue new JWT
            new_jwt = pyjwt.encode(
                {"sub": email, "exp": datetime.utcnow() + timedelta(hours=1)},
                JWT_SECRET,
                algorithm="HS256"
            )
            return {"refresh": True, "token": new_jwt}

        return {"name": user.name, "email": user.email, "picture": user.picture}
    except Exception as e:
        return {"error": str(e)}


# --- Step 4: Refresh JWT & Google access token if needed ---
@router.get("/refresh")
async def refresh_jwt(db: Session = Depends(get_db), authorization: str = Header(None)):
    """If Google refresh_token is available, issue a new JWT + access_token."""
    import jwt as pyjwt
    if not authorization:
        return {"error": "Missing Authorization header"}

    old_token = authorization.replace("Bearer ", "")
    try:
        data = pyjwt.decode(old_token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        email = data.get("sub")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"error": "User not found"}

        # Refresh Google access token if expired
        if datetime.utcnow() > user.token_expiry:
            async with httpx.AsyncClient() as client:
                token_data = {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "refresh_token": user.refresh_token,
                    "grant_type": "refresh_token"
                }
                token_resp = await client.post("https://oauth2.googleapis.com/token", data=token_data)
                new_tokens = token_resp.json()
                user.access_token = new_tokens.get("access_token")
                user.token_expiry = datetime.utcnow() + timedelta(seconds=new_tokens.get("expires_in", 3600))
                db.commit()

        # Issue a new short-lived JWT
        new_jwt = pyjwt.encode(
            {"sub": user.email, "exp": datetime.utcnow() + timedelta(hours=1)},
            JWT_SECRET,
            algorithm="HS256"
        )
        return {"token": new_jwt}
    except Exception as e:
        return {"error": str(e)}

from datetime import datetime, timedelta, timezone

@router.get("/calendar/today")
async def get_today_events(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        return {"error": "Missing Authorization header"}

    import jwt as pyjwt
    token = authorization.replace("Bearer ", "")
    try:
        data = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        email = data.get("sub")
        user = db.query(User).filter(User.email == email).first()

        events, message = await fetch_today_events_for_user(user)
        if events is None:
            return {"error": message}
        return {"events": events, "message": message}

    except Exception as e:
        return {"error": str(e)}