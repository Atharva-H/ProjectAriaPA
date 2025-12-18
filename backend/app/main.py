from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.db.database import engine
from app.db.models import Base
from app.routes.auth_routes import router as auth_router
from app.routes.whatsapp import router as whatsapp_router
from app.routes.user_routes import router as user_router
from app.routes.calendar_routes import router as calendar_router
from app.routes.integrations.google_calendar_routes import router as google_calendar_routes
from app.routes.integrations.google_gmail_routes import router as google_gmail_routes
from app.routes.integrations.integration_status_routes import router as integration_status_routes
from app.routes.integrations.accounting.tally_routes import router as tally_routes
from app.routes.integrations.accounting.accounting_routes import router as accounting_routes
from app.routes.contacts_routes import router as contacts_routes
from app.routes.media_routes import router as media_routes
from app.routes.chat_routes import router as chat_routes
from app.routes.task_routes import router as task_routes




from app.core.logging_config import setup_logging, user_context  # 👈 new import
from app.services.reminder_service import init_scheduler, shutdown_scheduler



# -------------------------------------------
# ⚙️ Initialize logging
# -------------------------------------------
setup_logging()
logger = logging.getLogger("ProjectAria.Backend")

# -------------------------------------------
# 🗄️ Database setup
# -------------------------------------------
Base.metadata.create_all(bind=engine)

# -------------------------------------------
# 🚀 Initialize FastAPI app
# -------------------------------------------
app = FastAPI(
    title="ProjectAria.PA API",
    description="Backend API for ProjectAria.PA — AI-based personal assistant for MSME CEOs.",
    version="1.0.0",
)

# -------------------------------------------
# 🌍 CORS setup
# -------------------------------------------
# CORS setup moved below logging middleware

# -------------------------------------------
# 🧩 Logging Middleware (inject user_id)
# -------------------------------------------
@app.middleware("http")
async def add_user_context_to_logs(request: Request, call_next):
    """
    Middleware to extract user_id from request headers or state
    and automatically include it in every log within this request context.
    """
    try:
        # 👇 This depends on your authentication logic
        user_id = None

        # Option 1: If auth sets user info in request.state
        if hasattr(request.state, "user"):
            user = getattr(request.state, "user")
            user_id = getattr(user, "id", None)

        # Option 2: If frontend sends a user_id in headers (for dev/testing)
        if not user_id:
            user_id = request.headers.get("X-User-ID")

        # Set context variable
        user_context.set(user_id)
        logger.info(f"Incoming request: {request.method} {request.url.path}")

        # Continue to route handler
        response = await call_next(request)

        # Retrieve whatever context was last set by the route
        current_user = user_context.get() or "anonymous"
        logger.info(f"Completed {request.method} {request.url.path} → {response.status_code} (user={current_user})")
        return response

    finally:
        # Always clear context at end of request
        user_context.set(None)


# -------------------------------------------
# 🌍 CORS setup (Must be outermost/last added)
# -------------------------------------------
# Production: Use specific origins from config
# Development: Allow all origins via regex
if settings.ENVIRONMENT == "production" and settings.CORS_ALLOW_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # DEVELOPMENT MODE: Allow all origins via regex to support credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# -------------------------------------------
# 🧭 Include all routers
# -------------------------------------------
app.include_router(auth_router)
app.include_router(whatsapp_router)
app.include_router(user_router)
app.include_router(calendar_router)
app.include_router(google_calendar_routes)
app.include_router(google_gmail_routes)
app.include_router(integration_status_routes)
app.include_router(tally_routes)
app.include_router(accounting_routes)
app.include_router(contacts_routes)
app.include_router(media_routes)
app.include_router(chat_routes)
app.include_router(task_routes)


# -------------------------------------------
# 🩺 Root health check
# -------------------------------------------
@app.get("/", tags=["Health"])
def root():
    logger.info("Health check endpoint called")
    return {"message": "✅ ProjectAria.PA backend is running successfully!"}

@app.on_event("startup")
async def startup_event():
    # start scheduler
    init_scheduler()
    # optionally load pending reminders from DB and reschedule (see below)

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_scheduler()