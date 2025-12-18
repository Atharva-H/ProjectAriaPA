from fastapi import APIRouter, Header, Depends
from sqlalchemy.orm import Session
from app.db import get_db, crud
from app.core.security import decode_jwt

router = APIRouter(prefix="/integrations", tags=["Integrations"])

@router.get("/status")
async def get_integration_status(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        return {"error": "Missing Authorization header"}

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        return {"error": "Invalid or expired token"}

    user = crud.get_user_by_email(db, data.get("sub"))
    if not user:
        return {"error": "User not found"}

    return {
        "google_calendar": {"connected": bool(user.google_calendar_token)},
        "google_gmail": {"connected": bool(user.google_gmail_token)},
        "whatsapp": {
            "connected": bool(user.whatsapp_verified),
            "number": user.whatsapp_no
        },
        "tally": {
            "connected": bool(user.tally_connected),
            "database_name": user.tally_database_name,
            "company": user.tally_company_name
        }
    }
