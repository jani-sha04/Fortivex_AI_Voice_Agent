"""
SQLAlchemy ORM Models for FORTIVEX AI Sales Agent
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base
import enum


class LeadStatus(str, enum.Enum):
    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"
    CONVERTED = "CONVERTED"
    LOST = "LOST"


class SentimentType(str, enum.Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(200), nullable=True)
    industry = Column(String(100), nullable=True)
    requirements = Column(Text, nullable=True)
    product_interest = Column(String(200), nullable=True)
    budget = Column(String(100), nullable=True)
    timeline = Column(String(100), nullable=True)
    intent = Column(String(100), nullable=True)
    sentiment = Column(String(20), nullable=True)
    lead_score = Column(Float, default=0.0)
    status = Column(String(20), default="COLD")
    notes = Column(Text, nullable=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("Conversation", back_populates="lead")
    appointments = relationship("Appointment", back_populates="lead")
