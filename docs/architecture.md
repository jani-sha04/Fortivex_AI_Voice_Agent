# FORTIVEX AI Sales Agent — Architecture Documentation

## System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           CUSTOMER INTERACTION LAYER                        │
│                                                                              │
│    Browser (React SPA)                                                       │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│    │Dashboard │ │AI Agent  │ │  Leads   │ │Knowledge │ │ Appointments │   │
│    │Analytics │ │Voice/Chat│ │Management│ │   Base   │ │  Scheduling  │   │
│    └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ REST API (HTTP/JSON + multipart)
                               │
┌──────────────────────────────▼──────────────────────────────────────────────┐
│                           FASTAPI BACKEND                                    │
│                                                                              │
│  Routes:  /api/agent  /api/voice  /api/knowledge  /api/leads                │
│           /api/appointments  /api/conversations  /api/dashboard              │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────────────────────────┐ │
│  │  VOICE PIPELINE  │  │              AI AGENT SERVICE                    │ │
│  │                  │  │                                                   │ │
│  │  Audio Upload    │  │  ┌──────────────────────────────────────────┐    │ │
│  │       ↓          │  │  │            GEMINI 1.5 FLASH              │    │ │
│  │  ffmpeg convert  │  │  │  • System prompt (sales persona)         │    │ │
│  │  to 16kHz WAV    │  │  │  • Conversation history (session)        │    │ │
│  │       ↓          │  │  │  • RAG context injection                 │    │ │
│  │  whisper.cpp     │  │  │  • Function/Tool calling                 │    │ │
│  │  (Metal/ARM64)   │  │  │  • Structured JSON output                │    │ │
│  │       ↓          │  │  └─────────────────┬────────────────────────┘    │ │
│  │  Text output     │  │                    │ Tool Calls                   │ │
│  │                  │  │  ┌─────────────────▼────────────────────────┐    │ │
│  │  Piper TTS       │  │  │           BUSINESS TOOLS                 │    │ │
│  │  (ONNX/ARM64)    │  │  │  create_lead() | book_appointment()      │    │ │
│  │       ↓          │  │  │  get_available_slots() | update_lead()   │    │ │
│  │  WAV audio out   │  │  │  search_knowledge_base() | call_summary()│    │ │
│  └──────────────────┘  │  └─────────────────┬────────────────────────┘    │ │
│                        │                    │                               │ │
│  ┌─────────────────────▼────────────────────▼──────────────────────────┐   │ │
│  │                      RAG ENGINE                                      │   │ │
│  │  ┌────────────────┐  ┌────────────────────────────────────────────┐ │   │ │
│  │  │ Document Ingest│  │       Semantic Search                      │ │   │ │
│  │  │  PDF/TXT       │  │  Query → embed → cosine sim → top-K chunks │ │   │ │
│  │  │  → chunk 500ch │  └────────────────────────────────────────────┘ │   │ │
│  │  │  → embed MiniLM│                                                  │   │ │
│  │  │  → store Chroma│  ┌──────────────────────────────────────────┐   │   │ │
│  │  └────────────────┘  │  ChromaDB (persistent local vector store) │   │   │ │
│  │                      │  all-MiniLM-L6-v2 (384-dim embeddings)   │   │   │ │
│  │                      └──────────────────────────────────────────┘   │   │ │
│  └──────────────────────────────────────────────────────────────────────┘   │ │
│                                                                              │ │
│  ┌──────────────────────────────────────────────────────────────────────┐   │ │
│  │                      SQLITE DATABASE                                 │   │ │
│  │  Leads | Conversations | Messages | Appointments | CallSummaries    │   │ │
│  │  KnowledgeDocuments | AgentSessions                                 │   │ │
│  └──────────────────────────────────────────────────────────────────────┘   │ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Frontend (React + Vite)
- **Dashboard**: Real-time analytics from `/api/dashboard/analytics`
- **AI Voice Agent**: WebRTC MediaRecorder → upload → Whisper STT → Gemini → Piper TTS
- **Lead Management**: CRUD with filtering, detail modal, inline status update
- **Knowledge Base**: Drag-drop upload, real-time processing status, ChromaDB management
- **Appointments**: Calendar-slot picker, duplicate prevention, status management
- **Call History**: Conversation transcripts with expandable summaries
- **Settings**: Configuration display, service status, setup instructions

### Backend Services

#### `GeminiService`
- Stateful chat using `model.start_chat(history=session_history)`
- Tool calling loop (up to 3 rounds) for autonomous business actions
- Structured JSON for lead extraction and sentiment analysis
- Retry with exponential backoff on rate limits
- Demo mode fallback when API key not configured

#### `RAGService`
- Document text extraction (pypdf for PDF, native for TXT)
- 500-char chunks with 50-char overlap and sentence boundary detection
- Local embeddings with `all-MiniLM-L6-v2` (90MB, runs fully locally)
- ChromaDB cosine similarity search, threshold 0.7
- Source citation in AI responses

#### `VoiceService`
- **WhisperService**: subprocess call to whisper.cpp binary with `-m model -f audio --no-timestamps`
- **PiperTTSService**: subprocess with Piper binary via stdin pipe
- Both have fallback modes (demo transcription, silent WAV) when binaries not installed

#### `AgentService`
- Orchestrates Gemini + RAG + tool execution
- Creates/retrieves conversations per session
- Saves all messages to database
- Quick sentiment check on every user message

## Data Flow: Voice Conversation

```
Browser mic → MediaRecorder (WebM) → POST /api/voice/transcribe
→ ffmpeg → 16kHz WAV → whisper.cpp → transcription text
→ POST /api/agent/chat (text + session_id)
→ RAG query (ChromaDB) → context
→ Gemini 1.5 Flash (context + history + message)
→ [optional tool calls: create_lead, book_appointment, etc.]
→ AI response text
→ POST /api/voice/speak → Piper TTS → WAV audio
→ Browser Audio API → plays to customer
```

## Database Schema

```sql
-- Conversations: one per session
conversations (id, session_id, customer_name, status, sentiment, lead_score, summary)

-- Messages: all conversation turns
messages (id, conversation_id, role, content, is_voice, created_at)

-- Leads: qualified customer data
leads (id, name, email, phone, company, industry, requirements, 
       product_interest, budget, timeline, intent, sentiment, 
       lead_score, status, conversation_id)

-- Appointments: booked slots
appointments (id, lead_id, customer_name, customer_email, 
              appointment_date, appointment_time, purpose, status)

-- Call Summaries: AI-generated post-conversation analysis
call_summaries (id, conversation_id, full_summary, requirements, 
                products_discussed, objections, sentiment, lead_score)

-- Knowledge Documents: uploaded files
knowledge_documents (id, filename, original_name, file_type, chunk_count, status)
```

## Security Architecture

- Gemini API key: environment variable only, never sent to frontend
- File uploads: validated by extension + MIME type + size limit (10MB)
- Database: SQLAlchemy ORM with parameterized queries
- CORS: restricted to known frontend origins
- No API secrets logged or exposed in responses

## Scalability Path

| Scale | Architecture |
|-------|-------------|
| 1-100 users | SQLite + single Uvicorn (current) |
| 100-10K | PostgreSQL + 3 Uvicorn + Nginx + Redis |
| 10K-100K | PostgreSQL HA + Kubernetes + CDN + Pinecone + Message queue |
| 100K+ | Multi-region + auto-scaling + dedicated AI gateway |
