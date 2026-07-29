# فکریار (Fikaryaar) — RAG Study & Deep Research Assistant

## One-Liner
A production-ready, multi-agent RAG (Retrieval-Augmented Generation) platform for students and researchers. Upload notes (PDF/DOCX/PPTX/MD/TXT) and get grounded answers, research paper analysis, and adaptive quizzes — all through a beautiful cyberpunk-academic UI.

## Core Agents (5 Specialized AI Assistants)
1. **Ustad (Tutor)** — Strict source-grounded Q&A from uploaded notes with footnoted citations, analogies, and key takeaways. Falls back to general knowledge when topic isn't in notes.
2. **Muhaqqiq (Researcher)** — Deep paper deconstruction (Delta, Core Intuition, Evidence Anchor, Blindspots), hypothesis cross-examination with confidence scores, and multi-document literature synthesis matrix.
3. **Imtehaan (Examiner)** — 5-level adaptive quizzes (Easy→Extreme), real-time evaluation scored /10, missed concepts analysis, and Urdu encouragement grade report.
4. **Darban (Doorkeeper)** — Intent classification & guardrails. Rejects off-topic queries gracefully.
5. **Mehakkim (Validator)** — Retrieval quality & coverage assessment.

## Tech Stack
- **Backend:** Python 3.11, FastAPI, LangChain, LangGraph, Chroma Vector DB
- **LLM:** Groq (llama-3.1-8b-instant) via langchain-groq — fast, generous free tier
- **Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (local, ~90MB, no API key)
- **Frontend:** Vanilla HTML5/CSS3/JS — no frameworks, no build step
- **Design System:** Deep Obsidian (#080A10) & Flame Amber (#FF6B00) cyberpunk-academic theme, Glassmorphism, custom particle canvas engine
- **Streaming:** Server-Sent Events (SSE) for real-time token output

## Key Features
- Multi-format upload: PDF, DOCX, PPTX, MD, TXT
- Drag-and-drop file ingestion with live knowledge base stats
- SSE streaming responses (tokens appear progressively)
- 5 specialized AI agents with instant mode switching
- Adaptive quiz engine with real-time grading
- Paper analysis with structural deconstruction
- Cross-examination of student hypotheses against papers
- Multi-document literature synthesis
- Off-topic refusal & guardrails
- Keep-alive mechanism for free-tier hosting

## Project Structure
```
├── app/
│   ├── agents/         # Agent implementations (ustad, muhaqqiq, imtehaan, darban, mehakkim)
│   ├── api/            # FastAPI routes (chat, quiz, upload, health)
│   ├── core/           # Config, logging
│   └── rag/            # Vector store, embeddings, ingestion, graph pipeline
├── static/
│   ├── index.html      # Single-page app shell
│   ├── css/styles.css  # Full design system
│   └── js/app.js       # Frontend controller (routing, SSE, particles, quiz)
├── pdf/                # Default study notes (auto-ingested on startup)
├── data/               # Uploads & Chroma DB persistence
├── Dockerfile          # Multi-stage Docker build (uv + gunicorn)
├── docker-compose.yml  # Local dev with volumes
└── .github/            # CI/CD pipeline
```

## How It Works
1. Upload notes via drag-and-drop or file picker
2. Notes are chunked, embedded, and stored in Chroma vector DB
3. Select an agent mode (Ustad/Muhaqqiq/Imtehaan)
4. Ask questions — the agent retrieves relevant chunks, grounds its answer, and streams it back with citations
5. For research papers: get structural analysis, cross-examine claims, synthesize multiple papers
6. For quizzes: agent detects topic, generates adaptive questions, evaluates answers, and produces grade report

## Getting Started
```bash
# 1. Clone & setup
git clone https://github.com/ayan-2007/FikarYaar.git
cd FikarYaar

# 2. Environment
cp .env.example .env
# Edit .env: set GROQ_API_KEY=gsk_your_key (get at https://console.groq.com)

# 3. Run
python -m uvicorn app.main:app --reload --port 8000

# 4. Open
open http://localhost:8000
```


## Requirements
- Python 3.11+ (or Docker)
- GROQ_API_KEY (free at console.groq.com — no credit card needed)
- ~90MB disk for embeddings model (auto-downloaded on first run)
