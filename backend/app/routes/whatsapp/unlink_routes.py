from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session  # ✅ ← this line was missing
from app.db import get_db, crud
from app.core.security import decode_jwt
from app.core.logging_config import user_context
import logging

router = APIRouter()
logger = logging.getLogger("ProjectAria.WhatsApp")

@router.post("/unlink")
async def unlink_whatsapp(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        raise HTTPException(401, "Invalid token")

    email = data.get("sub")
    user_context.set(email)
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")

    user.whatsapp_no = None
    user.whatsapp_verified = False
    db.commit()

    logger.info(f"Unlinked WhatsApp for {email}")
    return {"status": "unlinked"}
