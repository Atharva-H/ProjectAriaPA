# app/routes/media_routes.py
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Header, Depends
from sqlalchemy.orm import Session
from app.db import get_db, crud
from app.core.security import decode_jwt
from app.services.whisper_service import transcribe_audio

router = APIRouter(prefix="/media", tags=["Media"])

def _auth(db: Session, authorization: str):
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    data = decode_jwt(token)
    if not data:
        return None
    return crud.get_user_by_email(db, data.get("sub"))

@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...), authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _auth(db, authorization)
    if not user:
        return {"error": "Unauthorized"}
    os.makedirs("uploads", exist_ok=True)
    file_id = uuid.uuid4().hex
    path = os.path.join("uploads", f"{file_id}-{file.filename}")
    with open(path, "wb") as f:
        f.write(await file.read())
    text = await transcribe_audio(path)
    return {"transcript": text}


