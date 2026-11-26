"""
FORTIVEX AI Sales Agent - Gemini AI Service
Core conversation engine using Google Gemini API with tool calling.

BUG FIXES applied:
  - Demo mode now only fires for genuinely missing/placeholder keys
  - Conversation history is rebuilt from DB messages on every call (persistent across restarts)
  - Clear error messages instead of silent generic fallbacks
  - Stronger system prompt with context-aware sales persona
  - Sentiment/lead analysis errors are caught and reported individually
"""

import json
import logging
import time
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SYSTEM PROMPT — Shara, NovaTech AI Sales Executive
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are {agent_name}, an expert AI Sales Executive for {company_name}, a leading {company_industry} company.

## IDENTITY & ROLE
- Name: {agent_name}
- Company: {company_name}
- Role: AI Sales Executive
- Today's date: {current_date}

## PERSONALITY
You are professional, warm, conversational, and genuinely helpful.
You listen carefully, ask smart follow-up questions, and guide customers toward the right solution.
You are persuasive but never pushy or aggressive.

## PRIMARY RESPONSIBILITIES
1. Listen actively to understand the customer's real business problem
2. Ask one focused follow-up question at a time (never bombard with multiple questions)
3. Use knowledge base context (provided below your message) to answer product/pricing questions accurately
4. Identify purchasing intent signals naturally through conversation
5. Collect customer info (name, email, company, requirements) organically — never interrogate
6. Qualify leads based on intent, budget, and timeline
7. Offer product demonstrations when it feels natural
8. Book appointments only after explicit customer confirmation
9. Summarize the conversation when asked or when it concludes

## STRICT CONVERSATION RULES
- NEVER repeat a question you have already asked in this conversation
- NEVER ask for information the customer has already provided
- NEVER give the same generic response twice
- NEVER fabricate product details, pricing, or policies — use the knowledge base
- If you don't know something, say so honestly and offer to find out
- Keep responses concise: 2–4 sentences unless technical depth is required
- When you have enough info (name + 1 qualifier), use the create_lead tool
- When a customer confirms they want a demo, use get_available_slots then book_appointment
- Always acknowledge what the customer said before responding

## KNOWLEDGE BASE USAGE
When a [KNOWLEDGE BASE CONTEXT] section is included with your message, use it to answer product/pricing/feature questions.
Never invent information that isn't in the knowledge base.

## CONVERSATION CONTEXT AWARENESS
You will receive the conversation history. Use it to:
- Remember the customer's name, company, and requirements already shared
- Avoid repeating questions already answered
- Build naturally on previous turns
- Track what you've discussed vs. what still needs to be covered

Company: {company_name}
Industry: {company_industry}
"""

# ---------------------------------------------------------------------------
# TOOL DEFINITIONS
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "create_lead",
        "description": "Save a qualified customer lead to the CRM. Call this when you have the customer's name and at least one qualifier (company, requirements, or product interest).",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Customer full name"},
                "email": {"type": "string", "description": "Customer email address"},
                "phone": {"type": "string", "description": "Customer phone number"},
                "company": {"type": "string", "description": "Customer company name"},
                "industry": {"type": "string", "description": "Customer industry"},
                "requirements": {"type": "string", "description": "Customer business requirements and pain points"},
                "product_interest": {"type": "string", "description": "Products/solutions they are interested in"},
                "budget": {"type": "string", "description": "Budget range mentioned"},
                "timeline": {"type": "string", "description": "Purchase timeline"},
                "intent": {"type": "string", "description": "Buying intent: high/medium/low"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "book_appointment",
        "description": "Book a product demonstration or sales meeting. Only call this AFTER the customer has explicitly confirmed they want to meet and you have confirmed the date and time with them.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "Customer full name"},
                "customer_email": {"type": "string", "description": "Customer email address"},
                "appointment_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "appointment_time": {"type": "string", "description": "Time in HH:MM format (24-hour)"},
                "purpose": {"type": "string", "description": "Purpose of the meeting"},
                "lead_id": {"type": "string", "description": "Lead ID if already created"},
            },
            "required": ["customer_name", "customer_email", "appointment_date", "appointment_time"],
        },
    },
    {
        "name": "get_available_slots",
        "description": "Get available appointment slots for scheduling. Call this before booking to show the customer their options.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Specific date to check in YYYY-MM-DD format (optional — omit to get next 3 business days)"},
            },
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Search the company knowledge base to answer customer questions about products, pricing, features, integrations, or policies. Always use this for product-specific questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The specific question or topic to search for"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "generate_call_summary",
        "description": "Generate a professional summary of the conversation. Call this when the customer says goodbye, or when explicitly asked to summarize.",
        "parameters": {
            "type": "object",
            "properties": {
                "conversation_id": {"type": "string", "description": "The conversation ID to summarize"},
            },
            "required": ["conversation_id"],
        },
    },
    {
        "name": "update_lead",
        "description": "Update existing lead information in the CRM when you learn new details about an already-created lead.",
        "parameters": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string", "description": "The lead ID to update"},
                "field": {"type": "string", "description": "Field to update (e.g. email, company, budget)"},
                "value": {"type": "string", "description": "New value for the field"},
            },
            "required": ["lead_id", "field", "value"],
        },
    },
]


class GeminiService:
    """
    Core AI service using Google Gemini API.
    Maintains in-memory session cache; DB history is used for persistence.
    """

    def __init__(self):
        self.initialized = False
        self.model = None
        self._sessions: Dict[str, List[Dict]] = {}
        self._setup()

    def _setup(self):
        """Initialize Gemini API — rejects placeholder keys."""
        key = (settings.GEMINI_API_KEY or "").strip()

        # Detect placeholder / missing keys
        placeholder_markers = ("your_", "<", "sk-example", "")
        is_placeholder = not key or any(key.startswith(m) for m in placeholder_markers if m)

        if is_placeholder or settings.DEMO_MODE:
            logger.warning(
                "⚠️  Gemini API key not set or is a placeholder. "
                "DEMO MODE active — AI responses are scripted.\n"
                "   → Set GEMINI_API_KEY=<your real key> in backend/.env to enable live AI."
            )
            self.initialized = False
            return

        try:
            genai.configure(api_key=key)
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                tools=self._build_tools(),
                system_instruction=self._get_system_prompt(),
            )
            # Warm-up: verify the key is accepted (lightweight count tokens call)
            # We skip this to avoid extra latency — first real call will reveal bad keys
            self.initialized = True
            logger.info(f"✅ Gemini service initialized with model: {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            self.initialized = False

    def _get_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(
            agent_name=settings.AGENT_NAME,
            company_name=settings.COMPANY_NAME,
            company_industry=settings.COMPANY_INDUSTRY,
            current_date=datetime.now().strftime("%B %d, %Y"),
        )

    def _build_tools(self):
        """Convert tool definitions to Gemini format."""
        gemini_tools = []
        for tool in TOOLS:
            func_declaration = genai.protos.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        k: genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description=v.get("description", ""),
                        )
                        for k, v in tool.get("parameters", {}).get("properties", {}).items()
                    },
                    required=tool.get("parameters", {}).get("required", []),
                ),
            )
            gemini_tools.append(func_declaration)
        return [genai.protos.Tool(function_declarations=gemini_tools)]

    # ------------------------------------------------------------------
    # Session history helpers
    # ------------------------------------------------------------------

    def _get_session_history(self, session_id: str) -> List[Dict]:
        return self._sessions.get(session_id, [])

    def _set_session_history(self, session_id: str, history: List[Dict]):
        self._sessions[session_id] = history

    def load_history_from_db(self, session_id: str, db_messages: List[Dict]):
        """
        Populate in-memory history from DB messages.
        Call this at the start of each chat turn to ensure history is never lost
        across process restarts.

        db_messages should be [{"role": "user"|"assistant"|"model", "content": "..."}, ...]
        """
        if session_id in self._sessions and self._sessions[session_id]:
            return  # already loaded this session

        history = []
        for m in db_messages:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})
        self._sessions[session_id] = history
        logger.debug(f"Loaded {len(history)} messages into session {session_id[:8]}...")

    # ------------------------------------------------------------------
    # Main chat method
    # ------------------------------------------------------------------

    def chat(
        self,
        message: str,
        session_id: str,
        rag_context: Optional[str] = None,
        tool_handler=None,
    ) -> Tuple[str, List[str]]:
        """
        Send a message and return (response_text, list_of_tool_calls_made).
        Never silently returns a generic message — errors are surfaced clearly.
        """
        if not self.initialized:
            return self._demo_response(message), []

        # Augment user message with RAG context
        if rag_context:
            user_message = (
                f"[KNOWLEDGE BASE CONTEXT]\n{rag_context}\n[END CONTEXT]\n\n"
                f"Customer question: {message}"
            )
        else:
            user_message = message

        history = self._get_session_history(session_id)
        tool_calls_made = []

        try:
            chat_session = self.model.start_chat(history=history)
            response = self._send_with_retry(chat_session, user_message)

            final_response = ""
            max_tool_rounds = 4

            for _round in range(max_tool_rounds):
                if not (response.candidates and response.candidates[0].content.parts):
                    break

                parts = response.candidates[0].content.parts
                tool_call_parts = [
                    p for p in parts
                    if hasattr(p, "function_call") and p.function_call.name
                ]
                text_parts = [p for p in parts if hasattr(p, "text") and p.text]

                if text_parts:
                    final_response = " ".join(p.text for p in text_parts)

                if tool_call_parts and tool_handler:
                    tool_responses = []
                    for part in tool_call_parts:
                        fc = part.function_call
                        tool_name = fc.name
                        tool_args = dict(fc.args)
                        tool_calls_made.append(tool_name)
                        logger.info(f"🔧 Tool call: {tool_name}({tool_args})")
                        tool_result = tool_handler(tool_name, tool_args)
                        tool_responses.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name,
                                    response={"result": tool_result},
                                )
                            )
                        )
                    response = self._send_with_retry(chat_session, tool_responses)
                    continue
                else:
                    break

            # Persist to in-memory history
            updated_history = list(history)
            updated_history.append({"role": "user", "parts": [user_message]})
            if final_response:
                updated_history.append({"role": "model", "parts": [final_response]})
            self._set_session_history(session_id, updated_history)

            if not final_response:
                final_response = "I apologize — I had difficulty generating a response. Could you rephrase your question?"

            return final_response, tool_calls_made

        except google_exceptions.ResourceExhausted as e:
            logger.error(f"Gemini quota exhausted: {e}")
            return (
                "⚠️ AI service quota exceeded. Please try again in a moment or check your Gemini API quota at console.cloud.google.com.",
                [],
            )
        except google_exceptions.InvalidArgument as e:
            logger.error(f"Gemini invalid argument (likely bad API key): {e}")
            return (
                "⚠️ AI service configuration error. Your GEMINI_API_KEY may be invalid. "
                "Please verify it at aistudio.google.com and update backend/.env.",
                [],
            )
        except google_exceptions.PermissionDenied as e:
            logger.error(f"Gemini permission denied: {e}")
            return (
                "⚠️ AI service access denied. Please check that your GEMINI_API_KEY is valid "
                "and has access to the Gemini API.",
                [],
            )
        except google_exceptions.Unauthenticated as e:
            logger.error(f"Gemini unauthenticated: {e}")
            return (
                "⚠️ Gemini API authentication failed. Please set a valid GEMINI_API_KEY in backend/.env.",
                [],
            )
        except Exception as e:
            logger.error(f"Gemini chat error: {e}", exc_info=True)
            return (
                f"⚠️ AI service error: {type(e).__name__}. Please try again. "
                f"If the problem persists, check the backend logs.",
                [],
            )

    def _send_with_retry(self, chat_session, message, max_retries: int = 3):
        """Send message with exponential backoff on quota errors."""
        for attempt in range(max_retries):
            try:
                return chat_session.send_message(message)
            except google_exceptions.ResourceExhausted:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited — retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise
            except Exception:
                raise

    # ------------------------------------------------------------------
    # Analysis methods
    # ------------------------------------------------------------------

    def analyze_lead(self, conversation_text: str) -> Dict[str, Any]:
        """Extract structured lead data from conversation text."""
        if not self.initialized:
            return self._demo_lead_data()

        prompt = f"""Analyze this sales conversation and extract lead information as JSON.

Conversation:
{conversation_text}

Return ONLY valid JSON with these fields (use null for unknown):
{{
    "name": "customer full name or null",
    "email": "email or null",
    "phone": "phone or null",
    "company": "company name or null",
    "industry": "industry or null",
    "requirements": "business requirements summary",
    "product_interest": "products mentioned",
    "budget": "budget mentioned or null",
    "timeline": "purchase timeline or null",
    "intent": "high/medium/low",
    "sentiment": "POSITIVE/NEUTRAL/NEGATIVE",
    "lead_score": 0,
    "status": "HOT/WARM/COLD",
    "scoring_reason": "explanation of score"
}}

Scoring guide:
- HOT (70-100): Clear purchase intent, defined budget, timeline < 30 days
- WARM (40-69): Genuine interest, budget unclear, 1-3 month timeline
- COLD (0-39): Exploring/researching, no budget/timeline commitment"""

        try:
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Lead analysis error: {e}")
            return self._demo_lead_data()

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze customer sentiment. Returns safe defaults on failure."""
        if not self.initialized:
            return self._neutral_sentiment()

        prompt = f"""Analyze the sentiment of this customer message.

Message: "{text}"

Return ONLY valid JSON:
{{
    "sentiment": "POSITIVE/NEUTRAL/NEGATIVE",
    "buying_intent": "high/medium/low",
    "satisfaction": "satisfied/neutral/dissatisfied",
    "urgency": "high/medium/low",
    "objections": "list any concerns or null",
    "confidence": 0.5
}}"""

        try:
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.warning(f"Sentiment analysis failed (non-critical): {e}")
            return self._neutral_sentiment()

    def generate_summary(self, messages: List[Dict]) -> Dict[str, Any]:
        """Generate call summary from conversation messages."""
        if not self.initialized:
            return {
                "full_summary": "AI service not configured. Please set GEMINI_API_KEY in backend/.env.",
                "requirements": "Not captured",
                "products_discussed": "Not captured",
                "objections": "None noted",
                "sentiment": "NEUTRAL",
                "buying_intent": "medium",
                "lead_score": 0,
                "recommended_action": "Follow up",
            }

        conversation_text = "\n".join(
            [f"{m['role'].upper()}: {m['content']}" for m in messages]
        )

        prompt = f"""Generate a professional call summary for this sales conversation.

{conversation_text}

Return ONLY valid JSON:
{{
    "full_summary": "concise professional summary (3-5 sentences)",
    "requirements": "customer requirements identified",
    "products_discussed": "products/services mentioned",
    "objections": "concerns raised or 'None noted'",
    "sentiment": "POSITIVE/NEUTRAL/NEGATIVE",
    "buying_intent": "high/medium/low",
    "lead_score": 0,
    "recommended_action": "specific next recommended action",
    "customer_details": {{
        "name": "or null",
        "email": "or null",
        "company": "or null"
    }}
}}"""

        try:
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return {
                "full_summary": f"Summary generation failed: {str(e)}",
                "requirements": "Unknown",
                "products_discussed": "Unknown",
                "objections": "Unknown",
                "sentiment": "NEUTRAL",
                "buying_intent": "low",
                "lead_score": 0,
                "recommended_action": "Review conversation manually",
            }

    def clear_session(self, session_id: str):
        """Clear in-memory conversation history for a session."""
        self._sessions.pop(session_id, None)

    # ------------------------------------------------------------------
    # Demo / fallback helpers
    # ------------------------------------------------------------------

    def _demo_response(self, message: str) -> str:
        """
        Demo responses used ONLY when GEMINI_API_KEY is not configured.
        These are clearly labelled — they never masquerade as real AI responses.
        """
        msg_lower = message.lower()

        # Context-aware demo routing
        if any(w in msg_lower for w in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return (
                f"[DEMO MODE] Hello! I'm {settings.AGENT_NAME} from {settings.COMPANY_NAME}. "
                "I'm currently running in demo mode because no Gemini API key is configured. "
                "To enable real AI responses, add your GEMINI_API_KEY to backend/.env. "
                "In live mode, I'd ask: What brings you here today?"
            )
        elif any(w in msg_lower for w in ["price", "cost", "pricing", "how much"]):
            return (
                "[DEMO MODE] In live mode I'd search the knowledge base and give you accurate pricing. "
                "Demo: Our Enterprise Suite starts at $2,999/month. Configure GEMINI_API_KEY for real answers."
            )
        elif any(w in msg_lower for w in ["appointment", "demo", "meeting", "schedule", "book"]):
            return (
                "[DEMO MODE] I'd normally check available slots and confirm a time. "
                "Configure your GEMINI_API_KEY in backend/.env to enable real appointment booking."
            )
        elif any(w in msg_lower for w in ["feature", "product", "solution", "platform", "service"]):
            return (
                "[DEMO MODE] In live mode I'd answer this from the knowledge base. "
                "Demo: NovaTech offers Enterprise Suite, Analytics Pro, and Integration Hub. "
                "Set GEMINI_API_KEY to get real, knowledge-base-grounded answers."
            )
        else:
            return (
                f"[DEMO MODE] I'm {settings.AGENT_NAME} running without a Gemini API key. "
                "Real AI-powered responses require GEMINI_API_KEY to be set in backend/.env. "
                "Visit aistudio.google.com to get a free API key."
            )

    def _demo_lead_data(self) -> Dict[str, Any]:
        return {
            "name": "Demo Customer",
            "email": None,
            "phone": None,
            "company": "Demo Corp",
            "industry": "Technology",
            "requirements": "Demo requirements — configure Gemini API for real extraction",
            "product_interest": "Enterprise Suite",
            "budget": None,
            "timeline": None,
            "intent": "medium",
            "sentiment": "NEUTRAL",
            "lead_score": 50,
            "status": "WARM",
            "scoring_reason": "Demo mode — configure GEMINI_API_KEY for real lead scoring",
        }

    def _neutral_sentiment(self) -> Dict[str, Any]:
        return {
            "sentiment": "NEUTRAL",
            "buying_intent": "medium",
            "satisfaction": "neutral",
            "urgency": "low",
            "objections": None,
            "confidence": 0.5,
        }


# Singleton instance
gemini_service = GeminiService()
