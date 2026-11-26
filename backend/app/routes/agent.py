"""
Agent API routes - chat, voice chat, qualify, sentiment, session reset
"""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.schemas import ChatMessage, ChatResponse, QualifyRequest, SentimentRequest, SentimentResponse
from app.services.agent_service import agent_service
from app.services.gemini_service import gemini_service
from app.services.voice_service import whisper_service, piper_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage, db: Session = Depends(get_db)):
    """Send a text message to the AI sales agent and receive a response."""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        result = agent_service.chat(
            message=request.message,
            session_id=session_id,
            conversation_id=request.conversation_id,
            db=db,
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/voice")
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: str = Form(default=None),
    conversation_id: str = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    Full voice pipeline: audio → Whisper STT → Gemini → response text.
    Frontend can optionally call /api/voice/speak on the response text for TTS.
    """
    import os
    from pathlib import Path

    upload_dir = Path("uploads/audio")
    upload_dir.mkdir(parents=True, exist_ok=True)

    audio_data = await audio.read()
    if not audio_data:
        raise HTTPException(status_code=400, detail="Empty audio file.")

    ext = "webm"
    if audio.filename and "." in audio.filename:
        ext = audio.filename.rsplit(".", 1)[-1]

    temp_path = str(upload_dir / f"{uuid.uuid4()}.{ext}")
    try:
        with open(temp_path, "wb") as f:
            f.write(audio_data)

        transcription, success, is_demo_stt = whisper_service.transcribe(temp_path)

        if is_demo_stt or not success or not transcription.strip():
            # Whisper not available — return a helpful message without breaking
            return {
                "transcription": "",
                "response": (
                    "Voice transcription is not available yet. "
                    "Please run scripts/setup_whisper.sh to install whisper.cpp, "
                    "or use the text input to chat with me."
                ),
                "session_id": session_id or str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "is_demo": True,
                "stt_available": False,
                "tool_calls": [],
                "rag_sources": [],
            }

        # Transcription successful — run through AI pipeline
        sid = session_id or str(uuid.uuid4())
        result = agent_service.chat(
            message=transcription,
            session_id=sid,
            conversation_id=conversation_id,
            db=db,
        )

        return {
            "transcription": transcription,
            **result,
            "stt_available": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.post("/qualify")
async def qualify_lead(request: QualifyRequest, db: Session = Depends(get_db)):
    """Run lead qualification analysis on a conversation."""
    try:
        result = agent_service.qualify_lead(
            conversation_id=request.conversation_id,
            session_id=request.session_id,
            db=db,
        )
        return result
    except Exception as e:
        logger.error(f"Qualification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest, db: Session = Depends(get_db)):
    """Analyze sentiment of a customer message."""
    try:
        result = gemini_service.analyze_sentiment(request.text)
        return SentimentResponse(**result)
    except Exception as e:
        logger.error(f"Sentiment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def reset_session(session_id: str):
    """Clear in-memory conversation history for a session (force fresh context)."""
    gemini_service.clear_session(session_id)
    return {"message": f"Session {session_id} cleared.", "session_id": session_id}


@router.get("/status")
async def agent_status():
    """Check AI agent and voice service status."""
    return {
        "gemini_initialized": gemini_service.initialized,
        "demo_mode": not gemini_service.initialized,
        "model": settings_model_name(),
        "whisper_available": whisper_service.available,
        "piper_available": piper_service.available,
        "voice_pipeline_ready": whisper_service.available and piper_service.available,
    }


def settings_model_name() -> str:
    try:
        from app.config import settings
        return settings.GEMINI_MODEL if gemini_service.initialized else "demo"
    except Exception:
        return "unknown"
