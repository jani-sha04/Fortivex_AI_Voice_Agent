"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


# ============================================================
# Lead Schemas
# ============================================================

class LeadCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    requirements: Optional[str] = None
    product_interest: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    lead_score: Optional[float] = 0.0
    status: Optional[str] = "COLD"
    notes: Optional[str] = None
    conversation_id: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    requirements: Optional[str] = None
    product_interest: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    lead_score: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    industry: Optional[str]
    requirements: Optional[str]
    product_interest: Optional[str]
    budget: Optional[str]
    timeline: Optional[str]
    intent: Optional[str]
    sentiment: Optional[str]
    lead_score: float
    status: str
    notes: Optional[str]
    conversation_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Appointment Schemas
# ============================================================

class AppointmentCreate(BaseModel):
    lead_id: Optional[str] = None
    customer_name: str
    customer_email: str
    appointment_date: str  # YYYY-MM-DD
    appointment_time: str  # HH:MM
    purpose: Optional[str] = "Product Demo"
    notes: Optional[str] = None

    @field_validator("appointment_date")
    @classmethod
    def validate_date(cls, v):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("appointment_time")
    @classmethod
    def validate_time(cls, v):
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Time must be in HH:MM format")
        return v


class AppointmentUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    purpose: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    confirmed: Optional[bool] = None


class AppointmentResponse(BaseModel):
    id: str
    lead_id: Optional[str]
    customer_name: str
    customer_email: str
    appointment_date: str
    appointment_time: str
    purpose: Optional[str]
    status: str
    notes: Optional[str]
    confirmed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Agent / Chat Schemas
# ============================================================

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    conversation_id: str
    is_demo: bool = False
    lead_data: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[str]] = None


class QualifyRequest(BaseModel):
    conversation_id: str
    session_id: str


class SentimentRequest(BaseModel):
    text: str
    conversation_id: Optional[str] = None


class SentimentResponse(BaseModel):
    sentiment: str
    buying_intent: str
    satisfaction: str
    urgency: str
    objections: Optional[str] = None
    confidence: float


# ============================================================
# Knowledge Base Schemas
# ============================================================

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: Optional[int]
    chunk_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Conversation Schemas
# ============================================================

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    is_voice: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    session_id: str
    customer_name: Optional[str]
    customer_email: Optional[str]
    status: str
    sentiment: Optional[str]
    lead_score: float
    summary: Optional[str]
    buying_intent: Optional[str]
    created_at: datetime
    messages: Optional[List[MessageResponse]] = []

    class Config:
        from_attributes = True


# ============================================================
# Dashboard Schema
# ============================================================

class DashboardAnalytics(BaseModel):
    total_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    total_conversations: int
    total_appointments: int
    conversion_rate: float
    sentiment_distribution: Dict[str, int]
    recent_leads: List[LeadResponse]
    recent_appointments: List[AppointmentResponse]
