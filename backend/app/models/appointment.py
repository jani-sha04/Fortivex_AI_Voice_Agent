"""
Appointment model.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"), nullable=True)
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(200), nullable=False)
    appointment_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    appointment_time = Column(String(10), nullable=False)  # HH:MM
    purpose = Column(String(300), nullable=True, default="Product Demo")
    status = Column(String(20), default="scheduled")  # scheduled, completed, cancelled
    notes = Column(Text, nullable=True)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    lead = relationship("Lead", back_populates="appointments")
