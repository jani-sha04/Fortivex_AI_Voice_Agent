# FORTIVEX AI Sales Agent – Demo Walkthrough Script

> Use this script when presenting the project in a technical interview or demo session.
> Estimated demo time: 10–15 minutes.

---

## Pre-demo Checklist

- [ ] Backend running: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
- [ ] Frontend running: `cd frontend && npm run dev`
- [ ] Browser open at `http://localhost:5173`
- [ ] Real `GEMINI_API_KEY` set in `backend/.env` (for live AI demo)
- [ ] OR: `DEMO_MODE=true` for offline demo
- [ ] Sample data already seeded (run `bash scripts/seed_data.sh` if fresh)

---

## Step 1 – Dashboard (1 min)

**Say:** *"This is the main sales dashboard. It shows real-time metrics pulled from our SQLite database."*

**Show:**
- KPI cards: Total Leads, Active Conversations, Appointments Booked, Conversion Rate
- Lead quality chart (HOT / WARM / COLD breakdown)
- Recent activity feed
- Sentiment trend chart

**Key point:** *"All this data is live from the backend — no hardcoded values."*

---

## Step 2 – Knowledge Base (1–2 min)

**Navigate to:** Knowledge Base page

**Say:** *"Before the agent can answer product questions accurately, we load company documents into our RAG pipeline."*

**Show:**
- Two pre-loaded documents: `product_catalogue.txt` and `sales_faq.txt`
- Document status: `ready` with chunk count
- **Optionally:** Upload a new TXT or PDF file and watch it process

**Key point:** *"Documents are chunked, embedded with Sentence Transformers on Apple Silicon MPS, and stored in ChromaDB for semantic retrieval."*

---

## Step 3 – AI Agent Chat (4–5 min)

**Navigate to:** Agent Chat page

**Say:** *"Now let's talk to the AI sales agent — Aria from NovaTech Solutions."*

**Demo conversation flow:**

1. **Greeting:** Type `"Hello, I'm looking for an enterprise CRM solution"`
   - Agent greets professionally and asks about needs

2. **Product question:** Type `"What products do you offer and what's the pricing?"`
   - Agent searches knowledge base (RAG) and gives accurate answer

3. **Lead qualification:** Type `"My name is John Smith, I'm the CTO at Acme Corp. We have a team of 200 and need a scalable solution."`
   - Agent extracts info and may call `create_lead` tool → new lead appears in Leads page

4. **Demo booking:** Type `"I'd like to schedule a product demonstration"`
   - Agent offers slots, confirms, calls `book_appointment` tool

5. **Summary:** Type `"Thanks, that covers everything for now"`
   - Agent may call `generate_call_summary`

**Key point:** *"Notice the agent used tool calling — it autonomously called create_lead and book_appointment functions that wrote to our SQLite database."*

---

## Step 4 – Voice (1–2 min)

**Say:** *"The agent also supports voice input and output."*

**If whisper.cpp + Piper are configured:**
- Click the microphone button
- Speak a question
- Watch transcription appear, then AI response synthesized as audio

**If NOT configured (graceful degradation):**
- Show the voice status indicator: `STT: Not Ready | TTS: Not Ready`
- Explain: *"These require a one-time build of whisper.cpp with Apple Metal acceleration and downloading the Piper TTS model. The app handles their absence gracefully."*
- Show `scripts/setup_whisper.sh` and `scripts/setup_piper.sh`

---

## Step 5 – Leads CRM (1–2 min)

**Navigate to:** Leads page

**Show:**
- Lead table with score badges (HOT 🔴 / WARM 🟡 / COLD 🔵)
- Lead score (0-100) based on intent, budget, timeline
- Lead created by the agent during the demo conversation (if real Gemini key used)

**Key point:** *"The agent autonomously qualified this lead and scored it based on sentiment analysis and buying signal detection."*

---

## Step 6 – Appointments (30 sec)

**Navigate to:** Appointments page

**Show:**
- Appointment created by the agent during demo
- Status: `scheduled`
- Date, time, purpose

---

## Step 7 – Call History (1 min)

**Navigate to:** Call History page

**Show:**
- Conversation list
- Click a conversation → view full message thread
- Call summary panel (if summary was generated)

---

## Step 8 – Tests (30 sec)

**In terminal:**
```bash
cd backend
source venv/bin/activate
DEMO_MODE=true GEMINI_API_KEY=dummy pytest tests/test_api.py -v
```

**Show:** 20/20 tests passing

---

## Closing Points

- **Local-first:** All voice processing (whisper.cpp, Piper) runs on-device — no audio sent externally
- **Apple Silicon optimized:** Sentence Transformers use Apple MPS; whisper.cpp uses Metal
- **Free to run:** Only Gemini API (free tier) calls an external service
- **Production-ready architecture:** Separated services, Pydantic validation, SQLAlchemy ORM, 20 tests
- **Extensible:** Easy to add new knowledge documents, new tool calls, new agent personas

---

## Common Questions & Answers

**Q: Does it work without a Gemini API key?**
A: Yes — set `DEMO_MODE=true` in `.env`. The agent returns realistic scripted demo responses.

**Q: How accurate is the RAG retrieval?**
A: Using `all-MiniLM-L6-v2` with cosine similarity. Top-3 chunks are injected into every Gemini prompt. You can upload any PDF/TXT document.

**Q: Can you add more tools?**
A: Yes — add a function definition to `TOOLS` in `gemini_service.py` and handle it in `AgentService._handle_tool_call()`.

**Q: How does lead scoring work?**
A: Gemini analyzes the conversation and returns a JSON score 0-100. HOT = 70+, WARM = 40-69, COLD = below 40, based on intent clarity, budget mention, timeline, and sentiment.
