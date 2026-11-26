"""
Voice API routes - transcribe (STT) and speak (TTS)

BUG FIXES:
  - transcribe now returns is_demo correctly and does NOT return fake demo text
  - speak endpoint updated for 3-tuple return value from voice_service
  - /chat/voice endpoint added so voice and text both feed the same AI pipeline
"""

import os
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.voice_service import whisper_service, piper_service
from app.services.agent_service import agent_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["Voice"])

UPLOAD_DIR = Path("uploads/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/ogg", "audio/wav", "audio/mp4",
    "audio/mpeg", "audio/x-wav", "audio/x-m4a", "audio/webm;codecs=opus",
}
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe uploaded audio using whisper.cpp.
    Returns:
      { transcription: str, success: bool, is_demo: bool }

    When is_demo=True, transcription is "" — the frontend should NOT
    send an empty message to the AI.
    """
    content_type = audio.content_type or ""
    # Accept any audio/* content type (browser may send various variants)
    if not content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {content_type}. Use WebM, OGG, WAV, or MP4.",
        )

    audio_data = await audio.read()
    if len(audio_data) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file received.")
    if len(audio_data) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio file too large. Maximum 25MB.")

    ext = "webm"
    if audio.filename and "." in audio.filename:
        ext = audio.filename.rsplit(".", 1)[-1]
    temp_path = str(UPLOAD_DIR / f"{uuid.uuid4()}.{ext}")

    try:
        with open(temp_path, "wb") as f:
            f.write(audio_data)

        # whisper_service.transcribe now returns 3-tuple: (text, success, is_demo)
        transcription, success, is_demo = whisper_service.transcribe(temp_path)

        if is_demo:
            # Whisper not installed — tell the frontend clearly; return empty transcription
            return {
                "transcription": "",
                "success": False,
                "is_demo": True,
                "message": (
                    "Whisper.cpp is not installed. Run scripts/setup_whisper.sh to enable "
                    "real voice transcription. Use the text input to chat in the meantime."
                ),
            }

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Transcription failed. The audio may be too short or corrupted.",
            )

        return {
            "transcription": transcription,
            "success": True,
            "is_demo": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.post("/speak")
async def text_to_speech(text: str = Form(...)):
    """
    Generate speech audio from text using Piper TTS.
    Returns WAV audio. When Piper is not installed, returns a silent WAV.
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    text = text[:2000]  # Limit TTS text length

    # piper_service.synthesize now returns 3-tuple: (audio_bytes, success, is_demo)
    audio_data, success, is_demo = piper_service.synthesize(text)

    if not success or not audio_data:
        raise HTTPException(status_code=500, detail="Speech synthesis failed.")

    return Response(
        content=audio_data,
        media_type="audio/wav",
        headers={
            "Content-Disposition": "inline; filename=response.wav",
            "X-Demo-Mode": "true" if is_demo else "false",
            "X-Piper-Available": "true" if piper_service.available else "false",
        },
    )


@router.get("/status")
async def voice_status():
    """Check voice service availability."""
    return {
        "whisper_available": whisper_service.available,
        "piper_available": piper_service.available,
        "whisper_binary": whisper_service.binary,
        "whisper_model": whisper_service.model,
        "piper_binary": piper_service.binary,
        "piper_model": piper_service.model,
        "message": (
            "Voice pipeline fully operational."
            if (whisper_service.available and piper_service.available)
            else "Voice services not fully configured. Run setup_whisper.sh and setup_piper.sh."
        ),
    }
