"""
Conversations API routes
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.conversation import Conversation, Message, CallSummary
from app.schemas.schemas import ConversationResponse, MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(db: Session = Depends(get_db)):
    """List all conversations with summary info."""
    convs = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    result = []
    for conv in convs:
        messages = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at).all()
        conv_data = ConversationResponse.model_validate(conv)
        conv_data.messages = [MessageResponse.model_validate(m) for m in messages]
        result.append(conv_data)
    return result


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get a specific conversation with all messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    conv_data = ConversationResponse.model_validate(conv)
    conv_data.messages = [MessageResponse.model_validate(m) for m in messages]
    return conv_data


@router.get("/{conversation_id}/summary")
async def get_conversation_summary(conversation_id: str, db: Session = Depends(get_db)):
    """Get the call summary for a conversation."""
    summary = db.query(CallSummary).filter(
        CallSummary.conversation_id == conversation_id
    ).first()

    if not summary:
        raise HTTPException(status_code=404, detail="No summary found for this conversation")

    return {
        "id": summary.id,
        "conversation_id": summary.conversation_id,
        "full_summary": summary.full_summary,
        "requirements": summary.requirements,
        "products_discussed": summary.products_discussed,
        "objections": summary.objections,
        "sentiment": summary.sentiment,
        "buying_intent": summary.buying_intent,
        "lead_score": summary.lead_score,
        "recommended_action": summary.recommended_action,
        "customer_details": summary.customer_details,
        "appointment_info": summary.appointment_info,
        "created_at": summary.created_at.isoformat(),
    }


@router.post("/{conversation_id}/end")
async def end_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Mark conversation as ended and trigger summary generation."""
    from datetime import datetime
    from app.services.agent_service import agent_service

    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Generate summary
    result = agent_service._generate_summary_tool(conversation_id, db)
    return result
