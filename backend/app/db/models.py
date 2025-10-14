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