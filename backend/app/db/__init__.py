from .database import Base, engine, SessionLocal
from .models import *

# Dependency to get DB session (for FastAPI routes)
def get_db():
    from sqlalchemy.orm import Session
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
