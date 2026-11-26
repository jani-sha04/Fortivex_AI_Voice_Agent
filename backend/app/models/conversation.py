"""
Conversation and Message models.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    customer_name = Column(String(200), nullable=True)
    customer_email = Column(String(200), nullable=True)
    status = Column(String(20), default="active")  # active, completed, abandoned
    sentiment = Column(String(20), nullable=True)
    lead_score = Column(Float, default=0.0)
    summary = Column(Text, nullable=True)
    buying_intent = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    lead = relationship("Lead", back_populates="conversation", uselist=False)
    call_summary = relationship("CallSummary", back_populates="conversation", uselist=False)


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    is_voice = Column(Boolean, default=False)
    audio_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class CallSummary(Base):
    __tablename__ = "call_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    customer_details = Column(JSON, nullable=True)
    requirements = Column(Text, nullable=True)
    products_discussed = Column(Text, nullable=True)
    objections = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=True)
    buying_intent = Column(String(50), nullable=True)
    lead_score = Column(Float, default=0.0)
    recommended_action = Column(Text, nullable=True)
    appointment_info = Column(JSON, nullable=True)
    full_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("Conversation", back_populates="call_summary")
