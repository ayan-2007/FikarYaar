# Project Context — فکریار (Fikryar) RAG Study Chatbot

> Living state doc. Read this first if context is summarized / a new session starts.

## What this project is
A **study-only RAG chatbot**. It answers questions **strictly from uploaded notes**
(PDF/DOCX/PPTX/MD/TXT), with guardrails: off-topic refusal, doc-relevance grading,
source-cited answers. Frontend = premium "Fikryar" learning platform UI.

## Stack
- **Backend:** FastAPI + LangChain + LangGraph + Chroma + sentence-transformers (local embeddings)
- **LLM:** **Groq** (`langchain-groq`, model `llama-3.1-8b-instant`) — fast free tier
- **Frontend:** vanilla HTML/CSS/JS (served by FastAPI at `/`)

## CURRENT STATE (all done & verified)

### ✅ Backend fixes applied
1. **`.env` / `.env.example`** — swapped stale Gemini vars (`GOOGLE_API_KEY`/`GEMINI_MODEL`)
   for Groq vars (`GROQ_API_KEY`/`GROQ_MODEL`). Config code already read Groq, so the app
   was previously loading with an **empty** key. `.env` now has `GROQ_API_KEY=your_groq_api_key_here`.
2. **`app/rag/nodes/grade.py`** — was making **N sequential LLM calls** (one per chunk, TOP_K=5).
   Rewrote to grade ALL chunks in a **single batched LLM call**. Updated
   `app/core/prompts.py` `DOC_GRADER_PROMPT` to a per-snippet batch format.
3. Installed missing `langchain-groq` into the venv via `uv pip install langchain-groq`.

### ✅ Verified (offline, no key needed)
- `import app.main` → clean
- PDF `pdf/tony_gaddis_c++.pdf` loads → 1347 sections
- `build_graph()` compiles OK
- `_grade_batch` verdict parser unit-tested (handles messy model output)

### ✅ Frontend rebuilt (full Fikryar brand)
- `static/index.html` — app shell: sidebar + 5 views (home/learn/chat/explore/profile) + mobile bottom-nav + about modal
- `static/css/styles.css` — design system: burnt-orange palette, glassmorphism, dark theme, animations (orb breath/spin, particle glow, typer, ring progress)
- `static/js/app.js` — view router, canvas particle bg (neural lines), hero typer, SSE streaming chat, uploads, sources/health polling, WebAudio ambient sound + chimes, local growth stats

### ✅ Auto-ingestion verified
- Startup auto-ingests `pdf/tony_gaddis_c++.pdf` → 1347 chunks indexed
- Health endpoint confirms: chunks=1347, sources=1, LLM configured=true

## How to run (local)
```cmd
:: 1. put your Groq key in .env  (GROQ_API_KEY=gsk_...)
:: 2. start server
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
:: 3. open http://localhost:8000
```

## The 3 test questions (C++ textbook is loaded)
1. What is a class?
2. What are relationships between classes?
3. What is dynamic cast used for?
(All three are wired as clickable chips in the Chat view.)

## Key files map
| File | Role |
|------|------|
| `app/core/config.py` | Settings (reads `GROQ_API_KEY`, `GROQ_MODEL`, `TOP_K`, paths) |
| `app/core/prompts.py` | SYSTEM/INTENT/DOC_GRADER/REWRITE prompts |
| `app/rag/llm.py` | `get_llm()` / `get_grader_llm()` (ChatGroq) |
| `app/rag/graph.py` | LangGraph: rewrite→classify→retrieve→grade→generate |
| `app/rag/nodes/grade.py` | **batch grading (1 LLM call for all chunks)** |
| `app/rag/nodes/*.py` | rewrite, classify, retrieve, generate, refuse |
| `app/api/routes.py` | /api/chat, /chat/stream (SSE), /upload, /ingest, /sources, /health |
| `app/main.py` | FastAPI app, startup auto-ingest, static mount |
| `static/*` | Frontend (index.html, css/styles.css, js/app.js) |

## Notes / gotchas
- venv is **uv-managed**: `.venv\Scripts\python.exe`, install with `uv pip install ...`
- Embeddings model (~90MB) downloads on first run — cached after.
- The `langchain-google-genai` package is still in the venv (harmless leftover); Groq is what's used.
- `TOP_K=5` → now only **1** grading call instead of 5.
- Default notes dir is `pdf/` (copied from uploaded `data/uploads/`).

## Free Deployment Targets
| Platform | URL | Free Tier Limits | Best For |
|----------|-----|------------------|----------|
| **Render** | render.com | 750 hrs/mo, 512MB RAM, auto-sleep after 15min idle | Primary recommendation |
| **Railway** | railway.app | 500 hrs/mo, $5 credit/mo, no sleep | Alternative |
| **Fly.io** | fly.io | 3 shared-cpu-1x VMs free, 160GB monthly transfer | Docker-based |
| **Hugging Face Spaces** | huggingface.co/spaces | CPU basic, sleeps after 48h | ML-focused, Gradio/Streamlit native |