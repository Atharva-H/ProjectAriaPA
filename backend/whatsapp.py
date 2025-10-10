from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from twilio.rest import Client
from database import SessionLocal
from models import User
import os

router = APIRouter(prefix="/whatsapp")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/connect")
def connect_twilio(data: dict, db: Session = Depends(get_db)):
    """Connect a user's Twilio account"""
    user_email = data.get("email")
    sid = data.get("account_sid")
    token = data.get("auth_token")
    from_number = data.get("from_number")

    if not all([sid, token, from_number]):
        return {"error": "Missing required fields"}

    # Test credentials
    try:
        client = Client(sid, token)
        client.api.accounts(sid).fetch()
    except Exception as e:
        return {"error": f"Invalid Twilio credentials: {str(e)}"}

    # Store credentials (in real system: encrypt before saving)
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return {"error": "User not found"}

    user.twilio_sid = sid
    user.twilio_token = token
    user.twilio_from = from_number
    db.commit()

    return {"message": "Twilio connected successfully"}
