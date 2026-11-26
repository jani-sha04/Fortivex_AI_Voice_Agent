"""
Agent Orchestration Service
Ties together Gemini, RAG, Lead Qualification, and Business Actions.

BUG FIXES applied:
  - Loads DB message history into Gemini session before each call (persistent memory)
  - Sentiment analysis is non-blocking: failure doesn't break chat
  - is_demo flag correctly reflects Gemini initialization state
  - Voice chat endpoint added (transcribe → chat pipeline)
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.services.gemini_service import gemini_service
from app.services.rag_service import rag_service
from app.models.lead import Lead
from app.models.conversation import Conversation, Message, CallSummary
from app.models.appointment import Appointment

logger = logging.getLogger(__name__)

# Available appointment slots (business hours)
SLOT_HOURS = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]


class AgentService:
    """
    Orchestrates the AI sales agent:
    - Loads conversation history from DB into Gemini session (persistent memory)
    - Routes messages through RAG → Gemini
    - Handles tool calls for business actions
    - Maintains conversation state in DB
    """

    def chat(
        self,
        message: str,
        session_id: str,
        conversation_id: Optional[str],
        db: Session,
    ) -> Dict[str, Any]:
        """
        Process a customer message and return agent response.
        History is always reloaded from DB to ensure cross-restart persistence.
        """
        # 1. Get or create conversation record
        conversation = self._get_or_create_conversation(conversation_id, session_id, db)

        # 2. ── CRITICAL FIX: Load conversation history from DB into Gemini ──
        #    This ensures the AI remembers previous turns across process restarts
        previous_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
            .all()
        )
        db_history = [
            {"role": m.role, "content": m.content}
            for m in previous_messages
        ]
        gemini_service.load_history_from_db(session_id, db_history)

        # 3. Save customer message to DB
        self._save_message(conversation.id, "user", message, db)

        # 4. Query RAG for relevant context
        rag_context, sources = rag_service.query(message)

        # 5. Tool handler closure
        tool_calls_made = []

        def handle_tool(tool_name: str, args: Dict) -> Dict:
            tool_calls_made.append(tool_name)
            return self._execute_tool(tool_name, args, conversation.id, db)

        # 6. Get AI response from Gemini (with full history context)
        response_text, tools_used = gemini_service.chat(
            message=message,
            session_id=session_id,
            rag_context=rag_context if rag_context else None,
            tool_handler=handle_tool,
        )

        # 7. Save AI response to DB
        self._save_message(conversation.id, "assistant", response_text, db)

        # 8. Non-blocking sentiment analysis (failure doesn't break the response)
        try:
            sentiment_data = gemini_service.analyze_sentiment(message)
            if sentiment_data.get("sentiment"):
                conversation.sentiment = sentiment_data["sentiment"]
                conversation.buying_intent = sentiment_data.get("buying_intent")
                conversation.updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e:
            logger.warning(f"Sentiment analysis skipped (non-critical): {e}")

        return {
            "response": response_text,
            "session_id": session_id,
            "conversation_id": conversation.id,
            "is_demo": not gemini_service.initialized,
            "tool_calls": tools_used,
            "rag_sources": sources,
        }

    def qualify_lead(self, conversation_id: str, session_id: str, db: Session) -> Dict[str, Any]:
        """Run lead qualification on a full conversation."""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            return {"error": "Conversation not found"}

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

        conv_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in messages])
        lead_data = gemini_service.analyze_lead(conv_text)

        # Save or update lead
        existing_lead = db.query(Lead).filter(
            Lead.conversation_id == conversation_id
        ).first()

        if existing_lead:
            for field in ["name", "email", "phone", "company", "industry",
                          "requirements", "product_interest", "budget", "timeline",
                          "intent", "sentiment", "lead_score", "status"]:
                val = lead_data.get(field)
                if val is not None:
                    setattr(existing_lead, field, val)
            existing_lead.updated_at = datetime.now(timezone.utc)
            db.commit()
            lead = existing_lead
        else:
            lead = Lead(
                name=lead_data.get("name"),
                email=lead_data.get("email"),
                phone=lead_data.get("phone"),
                company=lead_data.get("company"),
                industry=lead_data.get("industry"),
                requirements=lead_data.get("requirements"),
                product_interest=lead_data.get("product_interest"),
                budget=lead_data.get("budget"),
                timeline=lead_data.get("timeline"),
                intent=lead_data.get("intent"),
                sentiment=lead_data.get("sentiment"),
                lead_score=float(lead_data.get("lead_score", 0)),
                status=lead_data.get("status", "COLD"),
                notes=lead_data.get("scoring_reason"),
                conversation_id=conversation_id,
            )
            db.add(lead)

        conversation.lead_score = float(lead_data.get("lead_score", 0))
        db.commit()
        return lead_data

    def _execute_tool(self, tool_name: str, args: Dict, conversation_id: str, db: Session) -> Dict:
        """Execute a business action tool called by the AI."""
        try:
            if tool_name == "search_knowledge_base":
                context, sources = rag_service.query(args.get("query", ""))
                return {"context": context or "No relevant information found in the knowledge base.", "sources": sources}

            elif tool_name == "get_available_slots":
                return self._get_available_slots(args.get("date"), db)

            elif tool_name == "create_lead":
                return self._create_lead_tool(args, conversation_id, db)

            elif tool_name == "book_appointment":
                return self._book_appointment_tool(args, db)

            elif tool_name == "update_lead":
                return self._update_lead_tool(args, db)

            elif tool_name == "generate_call_summary":
                return self._generate_summary_tool(conversation_id, db)

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return {"error": str(e)}

    def _get_available_slots(self, date_str: Optional[str], db: Session) -> Dict:
        """Return available appointment slots."""
        if not date_str:
            slots = []
            current = datetime.now()
            days_added = 0
            while days_added < 3:
                current += timedelta(days=1)
                if current.weekday() < 5:
                    date_key = current.strftime("%Y-%m-%d")
                    booked = db.query(Appointment).filter(
                        Appointment.appointment_date == date_key,
                        Appointment.status != "cancelled",
                    ).all()
                    booked_times = {a.appointment_time for a in booked}
                    available = [h for h in SLOT_HOURS if h not in booked_times]
                    slots.append({"date": date_key, "slots": available})
                    days_added += 1
            return {"available_slots": slots}
        else:
            booked = db.query(Appointment).filter(
                Appointment.appointment_date == date_str,
                Appointment.status != "cancelled",
            ).all()
            booked_times = {a.appointment_time for a in booked}
            available = [h for h in SLOT_HOURS if h not in booked_times]
            return {"date": date_str, "available_slots": available}

    def _create_lead_tool(self, args: Dict, conversation_id: str, db: Session) -> Dict:
        """Create a new lead from tool call."""
        email = args.get("email")
        if email and not self._validate_email(email):
            email = None  # Store lead without invalid email

        phone = args.get("phone")
        if phone and not self._validate_phone(phone):
            phone = None

        lead = Lead(
            name=args.get("name"),
            email=email,
            phone=phone,
            company=args.get("company"),
            industry=args.get("industry"),
            requirements=args.get("requirements"),
            product_interest=args.get("product_interest"),
            budget=args.get("budget"),
            timeline=args.get("timeline"),
            intent=args.get("intent", "medium"),
            conversation_id=conversation_id,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        logger.info(f"Lead created: {lead.id} for {args.get('name', 'unknown')}")
        return {
            "success": True,
            "lead_id": lead.id,
            "message": f"Lead successfully created for {args.get('name', 'customer')}",
        }

    def _book_appointment_tool(self, args: Dict, db: Session) -> Dict:
        """Book an appointment from tool call."""
        date = args.get("appointment_date")
        time_slot = args.get("appointment_time")
        email = args.get("customer_email")
        name = args.get("customer_name")

        if not all([date, time_slot, email, name]):
            return {"error": "Missing required appointment fields: customer_name, customer_email, appointment_date, appointment_time"}

        existing = db.query(Appointment).filter(
            Appointment.appointment_date == date,
            Appointment.appointment_time == time_slot,
            Appointment.status != "cancelled",
        ).first()

        if existing:
            return {
                "error": f"Slot {date} at {time_slot} is already booked. Please choose another time.",
                "suggestion": "Use get_available_slots to find open slots.",
            }

        appointment = Appointment(
            lead_id=args.get("lead_id"),
            customer_name=name,
            customer_email=email,
            appointment_date=date,
            appointment_time=time_slot,
            purpose=args.get("purpose", "Product Demo"),
            confirmed=True,
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        logger.info(f"Appointment booked: {appointment.id} for {name} on {date} at {time_slot}")
        return {
            "success": True,
            "appointment_id": appointment.id,
            "message": f"✅ Appointment confirmed for {name} on {date} at {time_slot}.",
        }

    def _update_lead_tool(self, args: Dict, db: Session) -> Dict:
        """Update lead information."""
        lead_id = args.get("lead_id")
        field = args.get("field")
        value = args.get("value")

        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": f"Lead {lead_id} not found"}

        if hasattr(lead, field):
            setattr(lead, field, value)
            lead.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {"success": True, "message": f"Updated {field} for lead {lead_id}"}
        else:
            return {"error": f"Invalid field: {field}"}

    def _generate_summary_tool(self, conversation_id: str, db: Session) -> Dict:
        """Generate and save call summary."""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

        msg_list = [{"role": m.role, "content": m.content} for m in messages]
        summary_data = gemini_service.generate_summary(msg_list)

        existing = db.query(CallSummary).filter(
            CallSummary.conversation_id == conversation_id
        ).first()

        summary_fields = [
            "full_summary", "requirements", "products_discussed", "objections",
            "sentiment", "buying_intent", "recommended_action", "customer_details",
        ]

        if existing:
            for f in summary_fields:
                setattr(existing, f, summary_data.get(f))
            existing.lead_score = float(summary_data.get("lead_score", 0))
        else:
            cs = CallSummary(
                conversation_id=conversation_id,
                full_summary=summary_data.get("full_summary"),
                requirements=summary_data.get("requirements"),
                products_discussed=summary_data.get("products_discussed"),
                objections=summary_data.get("objections"),
                sentiment=summary_data.get("sentiment"),
                buying_intent=summary_data.get("buying_intent"),
                lead_score=float(summary_data.get("lead_score", 0)),
                recommended_action=summary_data.get("recommended_action"),
                customer_details=summary_data.get("customer_details"),
            )
            db.add(cs)

        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.status = "completed"
            conv.summary = summary_data.get("full_summary", "")
            conv.ended_at = datetime.now(timezone.utc)

        db.commit()
        return {"success": True, "summary": summary_data}

    def _get_or_create_conversation(
        self, conversation_id: Optional[str], session_id: str, db: Session
    ) -> Conversation:
        if conversation_id:
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                return conv

        conv = Conversation(session_id=session_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def _save_message(
        self, conversation_id: str, role: str, content: str, db: Session, is_voice: bool = False
    ):
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            is_voice=is_voice,
        )
        db.add(msg)
        db.commit()

    def _validate_email(self, email: str) -> bool:
        import re
        pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _validate_phone(self, phone: str) -> bool:
        import re
        cleaned = re.sub(r"[\s\-\(\)\+]", "", phone)
        return cleaned.isdigit() and 7 <= len(cleaned) <= 15


agent_service = AgentService()
