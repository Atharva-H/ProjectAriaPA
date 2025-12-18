# app/services/whisper_service.py
import os
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger("ProjectAria.Whisper")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def transcribe_audio(file_path: str, language: Optional[str] = "en") -> str:
    try:
        # Check if file exists and get file size
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return ""
        
        file_size = os.path.getsize(file_path)
        logger.info(f"Transcribing audio file: {file_path} ({file_size} bytes)")
        
        if file_size == 0:
            logger.error(f"Audio file is empty: {file_path}")
            return ""
        
        # Determine MIME type from file extension
        # Whisper API supports: mp3, mp4, mpeg, mpga, m4a, wav, webm
        file_ext = os.path.splitext(file_path)[1].lower()
        mime_type_map = {
            '.webm': 'audio/webm',
            '.mp3': 'audio/mpeg',
            '.mp4': 'audio/mp4',
            '.m4a': 'audio/mp4',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.mpga': 'audio/mpeg',
            '.mpeg': 'audio/mpeg',
        }
        mime_type = mime_type_map.get(file_ext, 'audio/webm')  # Default to webm
        
        logger.info(f"Using MIME type: {mime_type} for extension: {file_ext}")
        
        # Open file and transcribe
        with open(file_path, "rb") as audio_file:
            # Whisper v1 transcription
            # Pass file as tuple: (filename, file_handle, mime_type)
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=(os.path.basename(file_path), audio_file, mime_type),
                language=language,
                response_format="text",
            )
        text = transcript  # already text
        logger.info(f"Transcribed audio {file_path} ({len(text)} chars)")
        return text
    except Exception as e:
        logger.exception(f"Whisper transcription failed: {e}")
        return ""


