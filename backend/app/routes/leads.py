"""
Leads API routes
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.lead import Lead
from app.schemas.schemas import LeadCreate, LeadUpdate, LeadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/leads", tags=["Leads"])


@router.get("", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all leads with optional filtering."""
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status.upper())
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Lead.name.ilike(search_term))
            | (Lead.email.ilike(search_term))
            | (Lead.company.ilike(search_term))
        )
    return query.order_by(Lead.created_at.desc()).all()


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: str, db: Session = Depends(get_db)):
    """Get a specific lead by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("", response_model=LeadResponse)
async def create_lead(lead_data: LeadCreate, db: Session = Depends(get_db)):
    """Create a new lead manually."""
    lead = Lead(**lead_data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: str, update: LeadUpdate, db: Session = Depends(get_db)):
    """Update lead information."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    from datetime import datetime, timezone
    lead.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lead)
    return lead
