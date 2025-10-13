# app/routes/user_routes.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from app.db import get_db, crud
from app.core.security import decode_jwt
from app.core.logging_config import user_context

router = APIRouter(prefix="/users", tags=["Users"])
logger = logging.getLogger("ProjectAria.Users")


# -------------------------------
# 📘 Models
# -------------------------------
class UserUpdateRequest(BaseModel):
    name: str | None = None
    picture: str | None = None


# -------------------------------
# 🔑 Helper to get authenticated user
# -------------------------------
def get_authenticated_user(authorization: str, db: Session):
    """Decode token, validate user, and attach context."""
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        logger.error(f"User not found in DB for email: {email}")
        raise HTTPException(status_code=404, detail="User not found")

    # Set logging context for rest of the request
    user_context.set(email)
    return user


# -------------------------------
# 🧩 Endpoints
# -------------------------------

@router.get("/me")
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Return the current logged-in user's details."""
    user = get_authenticated_user(authorization, db)
    logger.info(f"Fetched user profile: {user.email}")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "whatsapp_no": user.whatsapp_no,
        "whatsapp_verified": user.whatsapp_verified,
    }


@router.put("/me")
async def update_user(
    request: UserUpdateRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Update the logged-in user's name or picture."""
    user = get_authenticated_user(authorization, db)

    updated_fields = []
    if request.name and request.name != user.name:
        user.name = request.name
        updated_fields.append("name")
    if request.picture and request.picture != user.picture:
        user.picture = request.picture
        updated_fields.append("picture")

    if updated_fields:
        db.commit()
        db.refresh(user)
        logger.info(f"Updated user fields {updated_fields} for {user.email}")
    else:
        logger.info(f"No changes made for {user.email}")

    return {
        "message": "User updated successfully",
        "user": {"name": user.name, "picture": user.picture},
    }


@router.get("/")
async def list_users(db: Session = Depends(get_db)):
    """List all users (optional — can be restricted later)."""
    users = crud.get_all_users(db)
    logger.info(f"Fetched all users (count: {len(users)})")

    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "whatsapp_no": u.whatsapp_no,
            "whatsapp_verified": u.whatsapp_verified,
        }
        for u in users
    ]
