from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from app.db import get_db, crud
from app.core.security import decode_jwt
from app.core.logging_config import user_context
from app.services.twilio_service import send_whatsapp_message, make_verification_code

router = APIRouter()
logger = logging.getLogger("ProjectAria.WhatsApp")

class LinkRequest(BaseModel):
    number: str

class VerifyRequest(BaseModel):
    number: str
    code: str


@router.post("/link")
async def link_whatsapp(req: LinkRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
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

    number = req.number.strip()
    if not number.startswith("+"):
        raise HTTPException(400, "Phone number must be in E.164 format (e.g. +9198...)")

    whatsapp_to = f"whatsapp:{number}"
    code = make_verification_code()
    crud.set_whatsapp_verification(db, user, code, expires_in_minutes=10)

    send_whatsapp_message(whatsapp_to, f"Your ProjectAria.PA verification code: {code}")
    logger.info(f"Sent verification code to {number} for user {email}")
    return {"status": "sent"}


@router.post("/verify")
async def verify_whatsapp(req: VerifyRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
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

    if user.whatsapp_verify_code != req.code:
        raise HTTPException(400, "Invalid verification code")
    if user.whatsapp_verify_expires and user.whatsapp_verify_expires < datetime.utcnow():
        raise HTTPException(400, "Verification code expired")

    user.whatsapp_no = req.number.strip()
    user.whatsapp_verified = True
    user.whatsapp_verify_code = None
    user.whatsapp_verify_expires = None
    db.commit()

    logger.info(f"WhatsApp verified successfully for {email}")
    return {"status": "verified"}
