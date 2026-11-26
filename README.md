# FORTIVEX — Autonomous AI Sales Voice Agent

<div align="center">

![FORTIVEX Banner](docs/banner.png)

**A complete, production-ready AI-powered Sales Voice Agent**

Built for the FORTIVEX AI Private Limited technical challenge.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Gemini](https://img.shields.io/badge/Gemini-1.5--flash-4285F4?logo=google)](https://ai.google.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-orange)](https://www.trychroma.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🎯 Business Problem

Modern B2B sales teams are overwhelmed. Sales reps spend 65% of their time on non-selling activities: qualifying leads, answering repetitive questions, scheduling demos, and writing follow-up summaries. This costs enterprises hundreds of thousands in lost productivity.

## 💡 Solution

FORTIVEX is an **Autonomous AI Sales Voice Agent** that:
- Engages customers through voice or text conversations
- Retrieves accurate answers from your knowledge base using RAG
- Qualifies leads automatically with transparent scoring
- Books appointments with conflict-prevention
- Generates call summaries and sentiment analysis
- Provides a real-time sales dashboard

**Demo Company**: NovaTech Solutions (Enterprise Software) — configurable for any company.

---

## ✨ Features

| Feature | Technology | Status |
|---------|-----------|--------|
| AI Conversation Engine | Google Gemini 1.5 Flash | ✅ |
| RAG Knowledge Retrieval | ChromaDB + Sentence Transformers | ✅ |
| Speech-to-Text | whisper.cpp (local, Metal) | ✅ |
| Text-to-Speech | Piper TTS (local, ONNX) | ✅ |
| Lead Qualification & Scoring | Gemini Structured Output | ✅ |
| Sentiment Analysis | Gemini JSON Mode | ✅ |
| Appointment Booking | FastAPI + SQLite | ✅ |
| Tool/Function Calling | Gemini Function Calling | ✅ |
| Call Summarization | Gemini | ✅ |
| Analytics Dashboard | React + Recharts | ✅ |
| REST API | FastAPI + Swagger | ✅ |
| Demo Mode | No API key required | ✅ |

---

## 🏗️ Architecture

```
CUSTOMER
   │
   ▼
┌─────────────────────────────────────────┐
│          REACT FRONTEND (Vite)          │
│  Dashboard │ Agent │ Leads │ KB │ Appts │
└──────────────────┬──────────────────────┘
                   │ REST API
                   ▼
┌─────────────────────────────────────────┐
│          FASTAPI BACKEND                │
│                                         │
│  ┌────────────┐  ┌────────────────────┐ │
│  │   VOICE    │  │   AI AGENT SERVICE │ │
│  │ PROCESSING │  │                    │ │
│  │            │  │  ┌──────────────┐  │ │
│  │ whisper.cpp│  │  │  GEMINI API  │  │ │
│  │   (STT)    │  │  │  + Tool Call │  │ │
│  │            │  │  └──────────────┘  │ │
│  │  Piper TTS │  │         │          │ │
│  │   (output) │  │  ┌──────┴──────┐   │ │
│  └────────────┘  │  │ RAG ENGINE  │   │ │
│                  │  │  ChromaDB   │   │ │
│                  │  │  SentTrans  │   │ │
│                  │  └─────────────┘   │ │
│                  └────────────────────┘ │
│                          │              │
│                   ┌──────▼──────┐       │
│                   │   SQLite DB │       │
│                   │  SQLAlchemy │       │
│                   └─────────────┘       │
└─────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Frontend
- **React 18** + Vite 5 + JavaScript
- **Tailwind CSS** — utility-first styling
- **Lucide React** — icon library
- **Recharts** — analytics visualizations
- **Axios** — API communication
- **React Router DOM** — client-side routing

### Backend
- **Python 3.12** (compatible with 3.11+)
- **FastAPI** — async REST API framework
- **SQLAlchemy** — ORM with SQLite
- **Pydantic v2** — data validation
- **Uvicorn** — ASGI server

### AI & ML
- **Google Gemini 1.5 Flash** — conversation engine, lead analysis, sentiment, summaries
- **google-generativeai SDK** — official Gemini Python client
- **ChromaDB** — local vector database
- **Sentence Transformers** (all-MiniLM-L6-v2) — local embeddings (90MB)
- **whisper.cpp** — local Speech-to-Text (Apple Silicon Metal)
- **Piper TTS** — local neural Text-to-Speech (ONNX)

---

## 📋 Requirements

- macOS Apple Silicon M4 (or Intel Mac)
- Python 3.12+ (or 3.11)
- Node.js 18+
- 4GB+ free RAM (8GB+ recommended for all models)
- Gemini API key (free tier) — [Get one here](https://aistudio.google.com)

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/fortivex-ai-sales-agent.git
cd fortivex-ai-sales-agent
```

### 2. Configure environment

```bash
cp .env.example backend/.env
# Edit backend/.env and set:
# GEMINI_API_KEY=your_actual_key
# GEMINI_MODEL=gemini-1.5-flash
```

### 3. Set up the backend

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Set up the frontend

```bash
cd ../frontend
npm install
```

### 5. (Optional) Set up voice processing

```bash
# Speech-to-Text (whisper.cpp with Metal)
./scripts/setup_whisper.sh

# Text-to-Speech (Piper)
./scripts/setup_piper.sh
```

### 6. Seed sample data (optional)

```bash
bash scripts/seed_data.sh
```

---

## ▶️ Running the Application

### Start the backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Backend available at: http://localhost:8000
API documentation: http://localhost:8000/docs

### Start the frontend

```bash
cd frontend
npm run dev
```

Frontend available at: http://localhost:5173

---

## 🔧 Environment Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required for AI) | — |
| `GEMINI_MODEL` | Model name | `gemini-1.5-flash` |
| `DEMO_MODE` | Use demo responses without API | `false` |
| `COMPANY_NAME` | Demo company name | `NovaTech Solutions` |
| `AGENT_NAME` | AI agent name | `Aria` |
| `COMPANY_INDUSTRY` | Company industry | `Enterprise Software` |
| `DATABASE_URL` | SQLite URL | `sqlite:///./fortivex.db` |
| `WHISPER_MODEL_PATH` | Path to whisper model | `./whisper.cpp/models/ggml-base.en.bin` |
| `PIPER_MODEL_PATH` | Path to Piper voice model | `./piper/en_US-lessac-medium.onnx` |

---

## 📡 API Documentation

Full Swagger UI: http://localhost:8000/docs

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agent/chat` | Send message to AI agent |
| `POST` | `/api/agent/qualify` | Qualify leads from conversation |
| `POST` | `/api/agent/sentiment` | Analyze message sentiment |
| `POST` | `/api/voice/transcribe` | Audio → text (Whisper) |
| `POST` | `/api/voice/speak` | Text → audio (Piper) |
| `POST` | `/api/knowledge/upload` | Upload PDF/TXT to knowledge base |
| `GET` | `/api/knowledge/documents` | List uploaded documents |
| `GET` | `/api/leads` | List all leads |
| `POST` | `/api/leads` | Create lead manually |
| `GET` | `/api/appointments/available-slots` | Get open slots |
| `POST` | `/api/appointments` | Book an appointment |
| `GET` | `/api/conversations` | List all conversations |
| `GET` | `/api/dashboard/analytics` | Dashboard stats |
| `GET` | `/health` | Health check |

---

## 🎬 Demo Workflow

1. **Open** http://localhost:5173
2. **Navigate** to AI Voice Agent
3. **Type or speak**: "Hi, I need a CRM solution for my 50-person sales team. Budget is around $30K/year."
4. **Observe**: Aria responds, retrieves knowledge base info, asks follow-up questions
5. **Continue**: Provide your name and email
6. **Ask**: "Can I book a demo?"
7. **Observe**: AI calls `get_available_slots()` and `book_appointment()` tools
8. **Check Dashboard**: See your lead and appointment appear in real-time
9. **End conversation**: Click "End & Summarize" to generate call summary
10. **Review**: Check Call History for transcript and summary

---

## 🧪 Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v --tb=short
```

---

## 📊 Scalability Strategy

### Current (MVP)
- Single SQLite database
- Local ChromaDB vector store
- Local model inference
- Single Uvicorn process

### Production (100,000 users)

| Component | MVP | Production |
|-----------|-----|------------|
| Database | SQLite | PostgreSQL + read replicas |
| Vector DB | ChromaDB local | Pinecone / Weaviate cloud |
| Backend | 1 Uvicorn | 10+ instances + load balancer |
| AI Inference | Gemini API | Gemini with quota management |
| Queue | — | Redis + Celery |
| Cache | — | Redis distributed cache |
| Storage | Local files | AWS S3 / GCS |
| Container | — | Docker + Kubernetes |
| Monitoring | — | Datadog / Grafana + Prometheus |

**Estimated Production Cost (10k users/month)**:
- Gemini API: ~$50-200 (1.5-flash free tier up to 1M tokens/day)
- PostgreSQL (Cloud): $50-150/month
- Kubernetes cluster: $200-500/month
- Storage: $20-50/month
- **Total**: ~$320-900/month

---

## 🔒 Security

- API keys stored in `.env` (never committed)
- Backend-only Gemini access (never exposed to frontend)
- File upload validation (type + size)
- SQLAlchemy parameterized queries (no SQL injection)
- Input validation with Pydantic v2
- CORS configured for specific origins
- No customer PII logged

---

## ⚠️ Limitations

- Voice processing requires whisper.cpp and Piper setup (see scripts/)
- Gemini API requires free account at aistudio.google.com
- SQLite not suitable for concurrent production use (use PostgreSQL)
- whisper.cpp transcription is batch, not real-time streaming
- ChromaDB is single-process (use Pinecone/Weaviate for distributed)

---

## 🔮 Future Enhancements

- [ ] Real-time WebSocket streaming conversations
- [ ] Multi-language support (Whisper + Piper multilingual models)
- [ ] CRM integrations (Salesforce, HubSpot)
- [ ] Email follow-up automation
- [ ] A/B testing for conversation scripts
- [ ] Voice cloning for custom agent voices
- [ ] Multi-tenant SaaS deployment
- [ ] Mobile app (React Native)

---

## 📁 Project Structure

```
fortivex-ai-sales-agent/
├── frontend/              # React + Vite + Tailwind
│   └── src/
│       ├── pages/         # 7 pages (Dashboard, Agent, Leads, KB, Appts, History, Settings)
│       ├── components/    # Sidebar, UI components
│       ├── services/      # API client (axios)
│       └── hooks/         # useVoice, useAudioPlayer
├── backend/               # FastAPI application
│   └── app/
│       ├── main.py        # Entry point
│       ├── config.py      # Settings from .env
│       ├── routes/        # 7 route modules
│       ├── services/      # Gemini, RAG, Agent, Voice
│       ├── models/        # SQLAlchemy ORM models
│       └── schemas/       # Pydantic request/response schemas
├── knowledge_base/        # Sample company documents
│   └── sample_documents/
├── scripts/               # Setup scripts (whisper, piper, seed)
├── docs/                  # Architecture and reports
├── .env.example           # Environment template
└── README.md
```

---

## 📄 License

MIT License — See [LICENSE](LICENSE)

---

## 🏢 Built For

FORTIVEX AI Private Limited — Technical Interview Project  
Demonstrates: Generative AI · Agentic AI · RAG · Voice Processing · System Design · Business Automation
