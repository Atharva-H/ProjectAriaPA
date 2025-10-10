from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timedelta
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