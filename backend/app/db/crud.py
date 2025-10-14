# app/db/crud.py

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.db.models import User
from app.core.logging_config import user_context

logger = logging.getLogger("ProjectAria.CRUD")

# ------------------------
# 👤 User CRUD Operations
# ------------------------

def get_user_by_id(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    logger.debug(f"Fetched user by ID: {user_id} -> {bool(user)}")
    return user


def get_user_by_google_id(db: Session, google_id: str):
    user = db.query(User).filter(User.google_id == google_id).first()
    logger.debug(f"Fetched user by Google ID: {google_id} -> {bool(user)}")
    return user


def get_user_by_email(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    logger.debug(f"Fetched user by email: {email} -> {bool(user)}")
    return user


def create_user(
    db: Session,
    google_id: str,
    email: str,
    name: str,
    picture: str,
    access_token: str,
    refresh_token: str,
    token_expiry: datetime,
):
    user_context.set(email)
    user = User(
        google_id=google_id,
        email=email,
        name=name,
        picture=picture,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=token_expiry,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"🆕 Created new user: {email}")
    return user


def update_user_tokens(
    db: Session,
    user: User,
    access_token: str,
    refresh_token: str,
    expires_in: int,
):
    user_context.set(user.email)
    old_expiry = user.token_expiry
    user.access_token = access_token
    user.refresh_token = refresh_token
    user.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
    db.commit()
    db.refresh(user)
    logger.info(
        f"🔁 Updated tokens for {user.email} | Old expiry: {old_expiry} → New expiry: {user.token_expiry}"
    )
    return user


def get_all_users(db: Session):
    users = db.query(User).all()
    logger.info(f"Fetched all users (count={len(users)})")
    return users


def set_whatsapp_verification(
    db: Session,
    user: User,
    code: str,
    expires_in_minutes: int = 10,
):
    user_context.set(user.email)
    user.whatsapp_verify_code = code
    user.whatsapp_verify_expires = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    db.commit()
    db.refresh(user)
    logger.info(
        f"📲 Set WhatsApp verification code for {user.email} | Expires in {expires_in_minutes}m"
    )
    return user


def verify_whatsapp_code(db: Session, user: User, code: str):
    user_context.set(user.email)
    if (
        user.whatsapp_verify_code == code
        and user.whatsapp_verify_expires
        and user.whatsapp_verify_expires > datetime.utcnow()
    ):
        user.whatsapp_verified = True
        user.whatsapp_verify_code = None
        user.whatsapp_verify_expires = None
        db.commit()
        db.refresh(user)
        logger.info(f"✅ WhatsApp verified for {user.email}")
        return True

    logger.warning(f"❌ Invalid or expired WhatsApp code for {user.email}")
    return False


def get_user_by_whatsapp_no(db: Session, whatsapp_no: str):
    user = db.query(User).filter(User.whatsapp_no == whatsapp_no).first()
    logger.debug(f"Fetched user by WhatsApp no: {whatsapp_no} -> {bool(user)}")
    return user

# app/db/crud.py (append)

from datetime import datetime
from app.db.models import Reminder

def create_reminder(db: Session, user: User, event_id: str, run_at: datetime, job_id: str = None):
    reminder = Reminder(user_id=user.id, event_id=event_id, run_at=run_at, job_id=job_id)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder

def mark_reminder_sent(db: Session, reminder_id: int):
    r = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not r:
        return None
    r.sent = True
    db.commit()
    db.refresh(r)
    return r

def get_pending_reminders(db: Session):
    return db.query(Reminder).filter(Reminder.sent == False).all()
