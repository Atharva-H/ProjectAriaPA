import logging
import sys
import os
from contextvars import ContextVar
from app.core.config import settings

# Context variable for current user
user_context: ContextVar[str | None] = ContextVar("user_context", default=None)


class UserContextFilter(logging.Filter):
    """Ensures all logs have user_id and environment fields."""
    def filter(self, record: logging.LogRecord) -> bool:
        # Always safe-assign defaults
        record.user_id = user_context.get() or "anonymous"
        record.environment = getattr(settings, "ENVIRONMENT", "unknown")
        return True


def setup_logging():
    """Setup global logging with consistent context fields."""
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] [env=%(environment)s user_id=%(user_id)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    handlers = [console_handler]

    # Optional file handler
    if settings.LOG_TO_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.handlers = []  # clear old handlers
    for h in handlers:
        root_logger.addHandler(h)
        h.addFilter(UserContextFilter())  # attach the filter to each handler

    # Also attach filter globally for any other loggers
    root_logger.addFilter(UserContextFilter())

    # Quiet down noisy libs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
