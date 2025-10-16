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

from app.db.models import PendingAction
import json

def set_pending_action(db: Session, user_id: int, action_type: str, event_id: str, context: dict):
    db.query(PendingAction).filter(PendingAction.user_id == user_id).delete()
    pending = PendingAction(
        user_id=user_id,
        action_type=action_type,
        event_id=event_id,
        context=json.dumps(context),
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)
    return pending


def get_pending_action(db: Session, user_id: int):
    return db.query(PendingAction).filter(PendingAction.user_id == user_id).first()


def clear_pending_action(db: Session, user_id: int):
    db.query(PendingAction).filter(PendingAction.user_id == user_id).delete()
    db.commit()


# ------------------------
# 🔗 Google Integrations
# ------------------------
def update_calendar_tokens(db: Session, user: User, access_token: str, refresh_token: str, expiry_time: datetime):
    """Persist Google Calendar OAuth tokens for a user."""
    user_context.set(user.email)
    user.google_calendar_token = access_token
    if refresh_token:
        user.google_calendar_refresh = refresh_token
    # keep core tokens separate; do not overwrite login tokens here
    db.commit()
    db.refresh(user)
    logger.info(f"🔗 Saved Google Calendar tokens for {user.email}")
    return user


def update_gmail_tokens(db: Session, user: User, access_token: str, refresh_token: str, expiry_time: datetime):
    """Persist Gmail OAuth tokens for a user."""
    user_context.set(user.email)
    user.google_gmail_token = access_token
    if refresh_token:
        user.google_gmail_refresh = refresh_token
    db.commit()
    db.refresh(user)
    logger.info(f"🔗 Saved Gmail tokens for {user.email}")
    return user


# ------------------------
# 📇 Contacts CRUD
# ------------------------
from app.db.models import Contact, Task

def create_contact(db: Session, user: User, name: str, email: str = None, phone: str = None, designation: str = None, tags: str = None) -> Contact:
    contact = Contact(user_id=user.id, name=name, email=email, phone=phone, designation=designation, tags=tags)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    logger.info(f"👤 Added contact for {user.email}: {name}")
    return contact

def list_contacts(db: Session, user: User, q: str = None) -> list:
    query = db.query(Contact).filter(Contact.user_id == user.id)
    if q:
        like = f"%{q}%"
        query = query.filter((Contact.name.ilike(like)) | (Contact.email.ilike(like)) | (Contact.phone.ilike(like)))
    return query.order_by(Contact.name.asc()).all()

def update_contact(db: Session, contact_id: int, user: User, **fields) -> Contact:
    c = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
    if not c:
        return None
    for k, v in fields.items():
        if hasattr(c, k) and v is not None:
            setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c

def delete_contact(db: Session, contact_id: int, user: User) -> bool:
    deleted = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).delete()
    db.commit()
    return deleted > 0


# ------------------------
# ✅ Tasks
# ------------------------
def create_task(db: Session, user: User, title: str, description: str = None, due_at: datetime = None, source: str = None, link: str = None, created_from: str = None) -> Task:
    task = Task(user_id=user.id, title=title, description=description, due_at=due_at, source=source, link=link, created_from=created_from)
    db.add(task)
    db.commit()
    db.refresh(task)
    logger.info(f"📝 Task created for {user.email}: {title}")
    return task

def list_tasks(db: Session, user: User, status: str = None) -> list:
    query = db.query(Task).filter(Task.user_id == user.id)
    if status:
        query = query.filter(Task.status == status)
    return query.order_by(Task.due_at.asc().nulls_last()).all()

def complete_task(db: Session, user: User, task_id: int) -> Task:
    t = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not t:
        return None
    t.status = "done"
    db.commit()
    db.refresh(t)
    return t


# ------------------------
# 🔄 Google Token Refresh
# ------------------------
import httpx
from app.core.config import settings

async def refresh_google_access_token(refresh_token: str) -> dict:
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post("https://oauth2.googleapis.com/token", data=data)
        return res.json()
