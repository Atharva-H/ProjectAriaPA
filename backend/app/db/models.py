from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    picture = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    token_expiry = Column(DateTime, default=datetime.utcnow)

    # WhatsApp fields
    whatsapp_no = Column(String, unique=True, index=True, nullable=True)  # +919...
    whatsapp_verified = Column(Boolean, default=False)
    whatsapp_verify_code = Column(String, nullable=True)
    whatsapp_verify_expires = Column(DateTime, nullable=True)
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")

    google_calendar_token = Column(String, nullable=True)
    google_calendar_refresh = Column(String, nullable=True)
    google_gmail_token = Column(String, nullable=True)
    google_gmail_refresh = Column(String, nullable=True)



class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(String, nullable=True)   # calendar event id (optional)
    run_at = Column(DateTime, nullable=False)  # UTC time to run the reminder
    job_id = Column(String, nullable=True)     # APScheduler job id
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reminders")

class PendingAction(Base):
    __tablename__ = "pending_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action_type = Column(String)  # e.g., "calendar_conflict"
    event_id = Column(String)
    context = Column(String)  # store JSON context (slots, message, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True, index=True)
    designation = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # comma-separated simple tags
    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending | done | cancelled
    source = Column(String, nullable=True)  # gmail | mom | whatsapp | call
    link = Column(String, nullable=True)
    created_from = Column(String, nullable=True)  # message id / email id
    created_at = Column(DateTime, default=datetime.utcnow)