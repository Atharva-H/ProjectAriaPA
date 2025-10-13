import jwt
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logging_config import user_context  # 👈 new import for context
import logging

logger = logging.getLogger("ProjectAria.Security")

def create_jwt(email: str, expires_in_hours: int = 1):
    """Create a signed JWT for the given user (email as subject)."""
    payload = {
        "sub": email,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
    }

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    logger.info(f"JWT created for {email}")
    return token


def decode_jwt(token: str):
    """Decode JWT and attach user context for logging."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False},  # you can turn this on later
        )
        user_email = payload.get("sub")

        # Set context for logging
        if user_email:
            user_context.set(user_email)
            logger.info(f"JWT decoded successfully for user: {user_email}")
        else:
            logger.warning("JWT decoded but 'sub' missing")

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT expired")
        return None
    except jwt.InvalidTokenError:
        logger.error("Invalid JWT token")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error decoding JWT: {e}")
        return None
