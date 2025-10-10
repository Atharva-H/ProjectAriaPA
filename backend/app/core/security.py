import jwt
from datetime import datetime, timedelta
from app.core.config import settings

def create_jwt(email: str, expires_in_hours: int = 1):
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_jwt(token: str):
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None
