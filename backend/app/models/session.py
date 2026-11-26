"""
Agent session model.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.database.database import Base


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, unique=True, nullable=False)
    conversation_id = Column(String, nullable=True)
    history = Column(JSON, default=list)  # Store Gemini conversation history
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
