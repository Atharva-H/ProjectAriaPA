from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine
from app.db.models import Base
from app.routes.auth_routes import router as auth_router
from app.routes.whatsapp_routes import router as whatsapp_router
from app.routes.user_routes import router as user_router
from app.routes.calendar_routes import router as calendar_router  # If you later add calendar routes, import here

# If you later add Twilio routes, import here:
# from app.routes.twilio_routes import router as twilio_router

# Create all database tables (if not existing)
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="ProjectAria.PA API",
    description="Backend API for ProjectAria.PA — AI-based personal assistant for MSME CEOs.",
    version="1.0.0",
)

# Allowed frontend origins
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "https://your-deployed-frontend-url.com",  # optional for production
]

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(auth_router)
app.include_router(whatsapp_router)
app.include_router(user_router)   
app.include_router(calendar_router)   

# Root health check
@app.get("/", tags=["Health"])
def root():
    return {"message": "✅ ProjectAria.PA backend is running successfully!"}
