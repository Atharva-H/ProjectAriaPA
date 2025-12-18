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
    
    import logging
    logger = logging.getLogger("ProjectAria.Media")
    
    os.makedirs("uploads", exist_ok=True)
    file_id = uuid.uuid4().hex
    original_filename = file.filename or "audio.webm"
    
    # Determine file extension from content type or filename
    file_extension = "webm"
    if file.content_type:
        if "webm" in file.content_type:
            file_extension = "webm"
        elif "mp4" in file.content_type or "m4a" in file.content_type:
            file_extension = "m4a"
        elif "mp3" in file.content_type:
            file_extension = "mp3"
        elif "wav" in file.content_type:
            file_extension = "wav"
    elif original_filename:
        ext = original_filename.split(".")[-1].lower()
        if ext in ["webm", "m4a", "mp3", "mp4", "wav", "ogg"]:
            file_extension = ext
    
    path = os.path.join("uploads", f"{file_id}.{file_extension}")
    
    try:
        content = await file.read()
        file_size = len(content)
        logger.info(f"Received audio file: {original_filename} ({file_size} bytes, type: {file.content_type})")
        
        if file_size == 0:
            return {"error": "Empty file received", "transcript": ""}
        
        with open(path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved audio file to: {path}")
        text = await transcribe_audio(path)
        
        # Clean up temporary file after transcription
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Cleaned up temporary file: {path}")
        
        return {"transcript": text}
    except Exception as e:
        logger.exception(f"Error processing audio upload: {e}")
        # Clean up on error too
        if os.path.exists(path):
            os.remove(path)
        return {"error": str(e), "transcript": ""}


