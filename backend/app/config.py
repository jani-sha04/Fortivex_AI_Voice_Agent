"""
FORTIVEX AI Sales Agent - Application Configuration
Reads all settings from environment variables with safe defaults.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Database
    DATABASE_URL: str = "sqlite:///./fortivex.db"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Whisper.cpp
    WHISPER_MODEL_PATH: str = "./whisper.cpp/models/ggml-base.en.bin"
    WHISPER_BINARY_PATH: str = "./whisper.cpp/main"

    # Piper TTS
    PIPER_BINARY_PATH: str = "./venv/bin/piper"
    PIPER_MODEL_PATH: str = "./models/piper/en_US-lessac-medium.onnx"

    # Demo Mode
    DEMO_MODE: bool = False

    # Company Configuration
    COMPANY_NAME: str = "NovaTech Solutions"
    COMPANY_INDUSTRY: str = "Enterprise Software"
    AGENT_NAME: str = "Shara"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
