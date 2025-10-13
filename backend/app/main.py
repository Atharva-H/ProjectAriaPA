from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.db.database import engine
from app.db.models import Base
from app.routes.auth_routes import router as auth_router
from app.routes.whatsapp_routes import router as whatsapp_router
from app.routes.user_routes import router as user_router
from app.routes.calendar_routes import router as calendar_router

from app.core.logging_config import setup_logging, user_context  # 👈 new import

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
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "https://your-deployed-frontend-url.com",  # optional for production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# 🧭 Include all routers
# -------------------------------------------
app.include_router(auth_router)
app.include_router(whatsapp_router)
app.include_router(user_router)
app.include_router(calendar_router)

# -------------------------------------------
# 🩺 Root health check
# -------------------------------------------
@app.get("/", tags=["Health"])
def root():
    logger.info("Health check endpoint called")
    return {"message": "✅ ProjectAria.PA backend is running successfully!"}
