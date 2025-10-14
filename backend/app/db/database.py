# app/db/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# ---------------------------------
# 🔹 Load environment variables
# ---------------------------------
# Adjust this if your .env is in the project root:
# load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv()

# ---------------------------------
# 🔹 Database URL (PostgreSQL)
# ---------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:12345678@192.168.1.176:5432/project_aria_pa"
)

# ---------------------------------
# 🔹 SQLAlchemy Engine
# ---------------------------------
# For PostgreSQL, remove SQLite-specific args.
engine = create_engine(
    DATABASE_URL,
    pool_size=10,              # number of persistent connections
    max_overflow=20,           # extra connections for spikes
    pool_pre_ping=True,        # auto check if connections are alive
    future=True                # SQLAlchemy 2.0 style
)

# ---------------------------------
# 🔹 Session factory
# ---------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# ---------------------------------
# 🔹 Base model for ORM
# ---------------------------------
Base = declarative_base()


# ---------------------------------
# 🔹 Utility function for initializing DB (dev only)
# ---------------------------------
def init_db():
    """
    Creates all tables in the database.
    For development use only. In production, use Alembic migrations.
    """
    from app.db import models  # Import models before creating tables
    Base.metadata.create_all(bind=engine)
