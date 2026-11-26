"""
Appointments API routes
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.appointment import Appointment
from app.schemas.schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

SLOT_HOURS = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]


@router.get("/available-slots")
async def get_available_slots(db: Session = Depends(get_db)):
    """Get available appointment slots for the next 5 business days."""
    slots = []
    current = datetime.now()
    days_added = 0

    while days_added < 5:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday to Friday
            date_key = current.strftime("%Y-%m-%d")
            booked = db.query(Appointment).filter(
                Appointment.appointment_date == date_key,
                Appointment.status != "cancelled",
            ).all()
            booked_times = {a.appointment_time for a in booked}
            available = [h for h in SLOT_HOURS if h not in booked_times]
            slots.append({
                "date": date_key,
                "day": current.strftime("%A, %B %d"),
                "available_slots": available,
                "total_slots": len(SLOT_HOURS),
                "booked_count": len(booked_times),
            })
            days_added += 1

    return {"slots": slots}


@router.get("", response_model=List[AppointmentResponse])
async def list_appointments(db: Session = Depends(get_db)):
    """List all appointments."""
    return db.query(Appointment).order_by(
        Appointment.appointment_date.desc(), Appointment.appointment_time.desc()
    ).all()


@router.post("", response_model=AppointmentResponse)
async def create_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    """Book a new appointment."""
    # Check for duplicate
    existing = db.query(Appointment).filter(
        Appointment.appointment_date == data.appointment_date,
        Appointment.appointment_time == data.appointment_time,
        Appointment.status != "cancelled",
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Slot {data.appointment_date} at {data.appointment_time} is already booked.",
        )

    appointment = Appointment(**data.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    update: AppointmentUpdate,
    db: Session = Depends(get_db),
):
    """Update an appointment."""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    for field, value in update.dict(exclude_unset=True).items():
        setattr(appt, field, value)

    appt.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(appt)
    return appt


@router.delete("/{appointment_id}")
async def cancel_appointment(appointment_id: str, db: Session = Depends(get_db)):
    """Cancel an appointment."""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = "cancelled"
    appt.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "message": "Appointment cancelled."}
