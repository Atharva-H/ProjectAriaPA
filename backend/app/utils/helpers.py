from datetime import datetime, timezone, timedelta
import re
import logging

# -------------------------------
# 🧠 Logging Utility
# -------------------------------
def get_logger(name: str = "ProjectAria.PA"):
    """
    Returns a configured logger instance for consistent logging.
    Usage:
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# -------------------------------
# 📅 Time Utilities
# -------------------------------
def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def ist_now() -> datetime:
    """Return current time in IST timezone."""
    return utc_now() + timedelta(hours=5, minutes=30)


def format_datetime(dt: datetime) -> str:
    """Format datetime as readable string (for logs or UI)."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# -------------------------------
# 📱 Phone / WhatsApp Utilities
# -------------------------------
def normalize_whatsapp_number(number: str) -> str:
    """Ensure number is in E.164 format and prefixed correctly for Twilio."""
    if not number:
        return ""
    number = number.strip().replace(" ", "")
    if not number.startswith("+"):
        raise ValueError("Phone number must be in E.164 format (e.g. +919876543210)")
    if not number.startswith("whatsapp:"):
        number = f"whatsapp:{number}"
    return number


# -------------------------------
# 🔐 Token / String Helpers
# -------------------------------
def mask_token(token: str, visible: int = 4) -> str:
    """Mask a sensitive token for safe logging."""
    if not token:
        return ""
    return f"{token[:visible]}***{token[-visible:]}"


def sanitize_input(text: str) -> str:
    """Remove potential harmful characters (basic sanitization)."""
    if not text:
        return ""
    return re.sub(r"[^\w\s@+.-]", "", text)
