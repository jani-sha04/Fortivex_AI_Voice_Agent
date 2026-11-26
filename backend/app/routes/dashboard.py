"""
Dashboard analytics route
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.appointment import Appointment
from app.schemas.schemas import DashboardAnalytics, LeadResponse, AppointmentResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """Return dashboard analytics from real database data."""
    total_leads = db.query(Lead).count()
    hot_leads = db.query(Lead).filter(Lead.status == "HOT").count()
    warm_leads = db.query(Lead).filter(Lead.status == "WARM").count()
    cold_leads = db.query(Lead).filter(Lead.status == "COLD").count()
    converted = db.query(Lead).filter(Lead.status == "CONVERTED").count()
    total_conversations = db.query(Conversation).count()
    total_appointments = db.query(Appointment).filter(Appointment.status != "cancelled").count()

    conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0.0

    # Sentiment distribution
    sentiment_counts = db.query(
        Conversation.sentiment, func.count(Conversation.id)
    ).group_by(Conversation.sentiment).all()
    sentiment_dist = {
        "POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0, "Unknown": 0
    }
    for sentiment, count in sentiment_counts:
        key = sentiment if sentiment in sentiment_dist else "Unknown"
        sentiment_dist[key] += count

    # Recent leads (last 5)
    recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(5).all()

    # Recent appointments (next 5)
    recent_appointments = (
        db.query(Appointment)
        .filter(Appointment.status != "cancelled")
        .order_by(Appointment.appointment_date, Appointment.appointment_time)
        .limit(5)
        .all()
    )

    # Lead score average
    avg_score = db.query(func.avg(Lead.lead_score)).scalar() or 0.0

    # Monthly lead trend (last 6 months)
    from datetime import datetime, timedelta
    monthly_trend = []
    for i in range(5, -1, -1):
        month_start = (datetime.now().replace(day=1) - timedelta(days=i * 30))
        month_end = month_start.replace(day=28) + timedelta(days=4)
        count = db.query(Lead).filter(
            Lead.created_at >= month_start,
            Lead.created_at <= month_end,
        ).count()
        monthly_trend.append({
            "month": month_start.strftime("%b"),
            "leads": count,
        })

    return {
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "warm_leads": warm_leads,
        "cold_leads": cold_leads,
        "converted_leads": converted,
        "total_conversations": total_conversations,
        "total_appointments": total_appointments,
        "conversion_rate": round(conversion_rate, 1),
        "average_lead_score": round(float(avg_score), 1),
        "sentiment_distribution": sentiment_dist,
        "recent_leads": [LeadResponse.model_validate(l) for l in recent_leads],
        "recent_appointments": [AppointmentResponse.model_validate(a) for a in recent_appointments],
        "monthly_trend": monthly_trend,
    }
