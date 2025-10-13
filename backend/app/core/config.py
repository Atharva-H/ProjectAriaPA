import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # -------------------------
    # 🌍 Environment Settings
    # -------------------------
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # dev | staging | production
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # -------------------------
    # 🔐 Authentication
    # -------------------------
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    JWT_SECRET = os.getenv("JWT_SECRET")
    FRONTEND_URL = os.getenv("FRONTEND_URL")

    # -------------------------
    # 💬 Twilio Settings
    # -------------------------
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
    TWILIO_WEBHOOK_URL = os.getenv("TWILIO_WEBHOOK_URL")

    # -------------------------
    # 🧠 Logging Settings
    # -------------------------
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"


settings = Settings()
