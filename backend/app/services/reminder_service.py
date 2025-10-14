# app/services/reminder_service.py
import logging
import uuid
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from typing import Optional

from app.services.twilio_service import send_whatsapp_message
from app.core.logging_config import user_context
from app.db import crud
from app.db.database import SessionLocal

logger = logging.getLogger("ProjectAria.Reminder")

# Create a scheduler instance (will be started in main.py)
scheduler: Optional[AsyncIOScheduler] = None

def init_scheduler():
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()
        logger.info("APScheduler started.")

def shutdown_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shutdown.")

def _send_reminder(reminder_id: int, user_whatsapp: str, message: str):
    """
    Actual job executed by APScheduler. This function runs in the event loop.
    We use a DB session to mark the reminder as sent for traceability.
    """
    try:
        # user_context might be set if you want user-based log tags
        # user_context.set(user_email)  # optional if you pass email
        logger.info(f"Sending scheduled reminder to {user_whatsapp} (reminder_id={reminder_id})")
        send_whatsapp_message(user_whatsapp, message)

        # mark reminder sent in DB
        db = SessionLocal()
        try:
            crud.mark_reminder_sent(db, reminder_id)
        finally:
            db.close()

    except Exception as e:
        logger.exception(f"Error while sending reminder {reminder_id}: {e}")


def schedule_reminder(db, user, event_id: str, run_at_utc: datetime, message: str):
    """
    Schedule a one-time reminder.
    - db: SQLAlchemy Session (so we persist Reminder)
    - user: user object (must include whatsapp_no)
    - event_id: calendar event id (optional)
    - run_at_utc: datetime in UTC when reminder should fire
    - message: message to send
    """

    if not user.whatsapp_no:
        logger.warning("User does not have a WhatsApp number; skipping reminder scheduling.")
        return None

    if run_at_utc.tzinfo is None:
        run_at_utc = run_at_utc.replace(tzinfo=timezone.utc)

    # persist reminder
    reminder = crud.create_reminder(db, user, event_id, run_at_utc, job_id=None)

    # generate unique job id
    job_id = f"reminder-{reminder.id}-{uuid.uuid4().hex}"

    # ensure scheduler initialized
    init_scheduler()

    # schedule job (APScheduler expects naive or aware datetimes)
    scheduler.add_job(
        _send_reminder,
        'date',
        run_date=run_at_utc,
        args=[reminder.id, f"whatsapp:{user.whatsapp_no}", message],
        id=job_id,
        replace_existing=True
    )

    # store job_id
    reminder.job_id = job_id
    db.commit()
    db.refresh(reminder)

    logger.info(f"Scheduled reminder (id={reminder.id}) at {run_at_utc.isoformat()} job_id={job_id}")
    return reminder


def cancel_reminder(reminder):
    init_scheduler()
    try:
        if reminder.job_id:
            scheduler.remove_job(reminder.job_id)
        # Optionally delete/mark DB entry
    except JobLookupError:
        logger.warning("Job not found to cancel")
