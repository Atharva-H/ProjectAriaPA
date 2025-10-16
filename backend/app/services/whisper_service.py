# app/services/whisper_service.py
import os
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger("ProjectAria.Whisper")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def transcribe_audio(file_path: str, language: Optional[str] = "en") -> str:
    try:
        with open(file_path, "rb") as f:
            # Whisper v1 transcription
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language,
                response_format="text",
            )
        text = transcript  # already text
        logger.info(f"Transcribed audio {file_path} ({len(text)} chars)")
        return text
    except Exception as e:
        logger.exception(f"Whisper transcription failed: {e}")
        return ""


