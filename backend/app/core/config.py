# app/core/config.py

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
    GOOGLE_CALENDAR_REDIRECT_URI = os.getenv("GOOGLE_CALENDAR_REDIRECT_URI")
    GOOGLE_GMAIL_REDIRECT_URI = os.getenv("GOOGLE_GMAIL_REDIRECT_URI")
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

    # -------------------------
    # 🗄️ Tally Database Settings
    # -------------------------
    TALLY_DB_HOST = os.getenv("TALLY_DB_HOST", "localhost")
    TALLY_DB_PORT = int(os.getenv("TALLY_DB_PORT", "5432"))
    TALLY_DB_USER = os.getenv("TALLY_DB_USER", "readonly_user")
    TALLY_DB_PASSWORD = os.getenv("TALLY_DB_PASSWORD", "secure_password")
    TALLY_DB_MAX_CONNECTIONS = int(os.getenv("TALLY_DB_MAX_CONNECTIONS", "10"))
    TALLY_DB_MIN_CONNECTIONS = int(os.getenv("TALLY_DB_MIN_CONNECTIONS", "2"))

    # -------------------------
    # 📅 Calendar Working Hours
    # -------------------------
    WORK_START_HOUR = int(os.getenv("WORK_START_HOUR", "9"))  # 9 AM default
    WORK_END_HOUR = int(os.getenv("WORK_END_HOUR", "18"))    # 6 PM default


settings = Settings()
