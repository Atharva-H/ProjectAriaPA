from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.models import User

# ------------------------
# User CRUD Operations
# ------------------------

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_google_id(db: Session, google_id: str):
    return db.query(User).filter(User.google_id == google_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, google_id: str, email: str, name: str, picture: str,
                access_token: str, refresh_token: str, token_expiry: datetime):
    user = User(
        google_id=google_id,
        email=email,
        name=name,
        picture=picture,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=token_expiry
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_tokens(db: Session, user: User, access_token: str,
                       refresh_token: str, expires_in: int):
    user.access_token = access_token
    user.refresh_token = refresh_token
    user.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
    db.commit()
    db.refresh(user)
    return user

def get_all_users(db: Session):
    return db.query(User).all()

def set_whatsapp_verification(db: Session, user: User, code: str, expires_in_minutes: int = 10):
    user.whatsapp_verify_code = code
    user.whatsapp_verify_expires = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    db.commit()
    db.refresh(user)
    return user

def verify_whatsapp_code(db: Session, user: User, code: str):
    if (user.whatsapp_verify_code == code and 
        user.whatsapp_verify_expires and 
        user.whatsapp_verify_expires > datetime.utcnow()):
        user.whatsapp_verified = True
        user.whatsapp_verify_code = None
        user.whatsapp_verify_expires = None
        db.commit()
        db.refresh(user)
        return True
    return False

def get_user_by_whatsapp_no(db: Session, whatsapp_no: str):
    return db.query(User).filter(User.whatsapp_no == whatsapp_no).first()
