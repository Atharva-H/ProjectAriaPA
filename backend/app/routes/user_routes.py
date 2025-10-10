from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db import get_db, crud
from app.core.security import decode_jwt

router = APIRouter(prefix="/users", tags=["Users"])


# -------------------------------
# 📘 Models
# -------------------------------
class UserUpdateRequest(BaseModel):
    name: str | None = None
    picture: str | None = None


# -------------------------------
# 🧩 Endpoints
# -------------------------------

@router.get("/me")
async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Return the current logged-in user's details."""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        raise HTTPException(401, "Invalid or expired token")

    email = data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")

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
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        raise HTTPException(401, "Invalid or expired token")

    email = data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")

    if request.name:
        user.name = request.name
    if request.picture:
        user.picture = request.picture

    db.commit()
    db.refresh(user)
    return {"message": "User updated successfully", "user": {"name": user.name, "picture": user.picture}}


@router.get("/")
async def list_users(db: Session = Depends(get_db)):
    """List all users (optional — can be restricted later)."""
    users = crud.get_all_users(db)
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
