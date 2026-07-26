# Project Context — فکریار (Fikaryaar) RAG Study & Deep Research Assistant

> Living state doc. Updated with latest features, agent architectures, design system, and deployment configurations.

## What this project is
A **production-ready study & research RAG platform**. It provides:
1. **Ustad Agent (Interactive Tutor):** Strict source-grounded answers from uploaded notes (PDF/DOCX/PPTX/MD/TXT) with footnoted citations, analogies, key takeaways, and graceful fallback to general knowledge when topics aren't in notes.
2. **Muhaqqiq Agent (Research Paper Assistant):** Deep structural deconstruction (The Delta, Core Intuition, Evidence Anchor, Blindspots & Critique), fact-checking student hypotheses/claims against paper chunks (with confidence scores & counter-arguments), and multi-document literature synthesis matrix.
3. **Imtehaan Agent (Exam & Assessment):** 5-level adaptive quizzes (Easy to Extreme), real-time evaluation with scoring out of 10, missed concepts analysis, correct explanations, and Urdu encouragement grade report.
4. **Darban & Mehakkim Agents:** Doorkeeper guardrails (intent classification, off-topic refusal) and document quality validator.

## Stack
- **Backend:** FastAPI + LangChain + LangGraph + Chroma Vector DB + sentence-transformers (`all-MiniLM-L6-v2` local embeddings)
- **LLM:** **Groq** (`langchain-groq`, model `llama-3.1-8b-instant`) — fast, high-performance inference
- **Frontend:** HTML5 + Vanilla CSS (Custom Design System with Glassmorphism, Deep Obsidian & Flame Amber themes) + Vanilla JS (View router, Canvas Particle Engine, SSE streaming, drag-and-drop ingestion)

## CURRENT STATE (Production Ready & Fully Verified)

### ✅ Agent Architecture & Backend Enhancements
- **Agent Export Unification (`app/agents/__init__.py` & `agents/__init__.py`):** Unified re-exports across both agent packages (`classify`, `validate`, `stream_answer`, `start_quiz`, `evaluate_answer`, `analyze_paper`, `cross_examine_claim`, `synthesize_multiple_papers`).
- **Muhaqqiq Deep Research Engine (`app/agents/muhaqqiq.py`):** Added robust multi-strategy JSON parser, safe fallback objects, paper deconstruction, hypothesis cross-examination, and literature synthesis across multiple uploaded papers.
- **Enhanced SSE Stream Handler (`app/api/routes.py`):** Enhanced `/api/chat/stream` for `muhaqqiq` & `ustad`, handling empty knowledge bases gracefully and auto-defaulting queries when in paper analysis / synthesis modes.
- **Imtehaan Assessment Engine (`app/agents/imtehaan.py` & `/api/quiz/*`):** Topic auto-detection, single-file or multi-file quiz scope, instant evaluations, and grade reporting.

### ✅ Frontend UI / UX Elevation
- **Design System (`static/css/styles.css`):** Built a high-end Deep Obsidian (`#080A10`) & Flame Amber (`#FF6B00`) cyberpunk-academic theme with Emerald (`#00E5A3`) success indicators and Indigo (`#6366F1`) research badges. Glassmorphism cards, glowing active states, and custom micro-animations.
- **Typography Upgrade (`static/index.html`):** Integrated Google Fonts (`Outfit`, `Inter`, `JetBrains Mono`, `Noto Nastaliq Urdu`).
- **Seamless Interactive UX (`static/js/app.js`):**
  - Instant agent mode switching (Ustad vs. Muhaqqiq).
  - Dynamic button activation so paper analysis/synthesis can be triggered with one click.
  - Interactive canvas particle field and demo typewriter.
  - Live Knowledge Base stats polling & drag-and-drop file uploader.

## How to run locally
```cmd
:: 1. Verify GROQ_API_KEY in .env
:: GROQ_API_KEY=gsk_...

:: 2. Start Uvicorn server
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

:: 3. Access local web application
http://localhost:8000
```

## Key Files Map
| File | Role |
|------|------|
| `app/agents/muhaqqiq.py` | Research Paper Study Assistant (Paper Analysis, Cross-Examination, Multi-Doc Synthesis) |
| `app/agents/ustad.py` | Master Tutor Agent (Grounded RAG Q&A with footnotes & fallback mode) |
| `app/agents/imtehaan.py` | Examiner Agent (Quiz Generation & Interactive Evaluation) |
| `app/agents/darban.py` | Doorkeeper Agent (Intent Classification & Guardrails) |
| `app/agents/mehakkim.py` | Validator Agent (Retrieval Quality & Coverage Assessment) |
| `app/api/routes.py` | API endpoints (/api/chat/stream, /api/quiz/*, /api/upload, /api/health) |
| `app/rag/graph.py` | LangGraph RAG workflow pipeline |
| `static/index.html` | App Shell (Home, Chat, Quiz views, Knowledge Base panel, Modal) |
| `static/css/styles.css` | Design System (Obsidian/Amber themes, Glassmorphism, Typography, Animations) |
| `static/js/app.js` | Frontend Controller (Agent routing, Canvas particles, SSE streaming, Quiz logic) |