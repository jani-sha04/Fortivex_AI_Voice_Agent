"""
FORTIVEX AI Sales Agent - FastAPI Application Entry Point
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("🚀 Starting FORTIVEX AI Sales Agent...")

    # Initialize database
    init_db()
    logger.info("✅ Database initialized")

    # Create required directories
    os.makedirs("uploads/audio", exist_ok=True)
    os.makedirs("uploads/documents", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    os.makedirs("chroma_db", exist_ok=True)

    logger.info(f"🤖 Agent: {settings.AGENT_NAME} | Company: {settings.COMPANY_NAME}")
    logger.info(f"🧠 AI Model: {settings.GEMINI_MODEL}")
    logger.info(f"🎭 Demo Mode: {settings.DEMO_MODE or not settings.GEMINI_API_KEY}")

    yield

    logger.info("👋 Shutting down FORTIVEX AI Sales Agent...")


app = FastAPI(
    title="FORTIVEX AI Sales Agent API",
    description="""
## FORTIVEX - Autonomous AI Sales Voice Agent

A complete AI-powered sales agent with:
- 🤖 Gemini AI conversation engine
- 🎙️ Whisper.cpp speech-to-text
- 🔊 Piper TTS voice synthesis
- 📚 RAG knowledge retrieval (ChromaDB)
- 🎯 Lead qualification and scoring
- 📅 Appointment booking
- 📊 Analytics dashboard

Built for local deployment on Apple Silicon M4.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.routes import agent, voice, knowledge, leads, appointments, conversations, dashboard

app.include_router(agent.router)
app.include_router(voice.router)
app.include_router(knowledge.router)
app.include_router(leads.router)
app.include_router(appointments.router)
app.include_router(conversations.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "FORTIVEX AI Sales Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "agent": settings.AGENT_NAME,
        "company": settings.COMPANY_NAME,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    from app.services.gemini_service import gemini_service
    from app.services.rag_service import rag_service
    from app.services.voice_service import whisper_service, piper_service

    return {
        "status": "healthy",
        "services": {
            "gemini": gemini_service.initialized,
            "rag": rag_service.is_ready,
            "whisper": whisper_service.available,
            "piper": piper_service.available,
        },
        "demo_mode": not gemini_service.initialized,
    }
