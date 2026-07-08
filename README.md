# 📚 StudyBuddy — RAG Study Chatbot

A **study-only** AI chatbot that answers **strictly from your own notes**
(PDF / DOCX / Markdown / TXT). No hallucinations, no off-topic chats — it
literally refuses anything that isn't about studying the material you upload.

Built with **LangChain + LangGraph + sentence-transformers + Chroma**, a
**FastAPI** backend, and a unique animated **vanilla HTML/CSS/JS** frontend.

![stack](https://img.shields.io/badge/Python-3.11+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688) ![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-ff6b6b)

---

## ✨ Features

- **Study-only by design** — a 3-layer guardrail (rule filter → intent classifier
  → relevance grader + system-prompt lockdown) keeps it locked to your notes.
- **Multi-format ingestion** — PDF, DOCX, Markdown, plain text.
- **Upload your own notes** in-app; they're chunked, embedded, and searchable
  instantly. Drag & drop works too.
- **Cited answers** — every reply shows which note(s) it came from.
- **Streaming responses** (SSE) with a typewriter feel.
- **Local embeddings** (sentence-transformers, all-MiniLM-L6-v2) — private, free.
- **Google Gemini** (free tier) for the answer LLM.
- **3 themes** (Midnight / Aurora / Paper), animated aurora background,
  glassmorphism UI, fully responsive.
- **Sources panel** with per-file delete and a live knowledge-base counter.
- **Production Dockerfile** + **Render blueprint** for one-click free hosting.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Browser (static HTML/CSS/JS)                            │
│   └─ chat (SSE) · upload · sources · themes              │
└───────────────┬──────────────────────────────────────────┘
                │ HTTPS /api/*
┌───────────────▼──────────────────────────────────────────┐
│  FastAPI  (app/main.py, app/api/routes.py)               │
│   • CORS · static mount · startup auto-ingest            │
└───────────────┬──────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────┐
│  LangGraph RAG pipeline  (app/rag/graph.py)              │
│   rewrite → classify → retrieve → grade → generate       │
│                    └──────────────► refuse (off-topic)   │
│                                   └──────► refuse (none) │
└───────────────┬──────────────────────────────────────────┘
                │
   ┌────────────┼─────────────┬───────────────┐
   ▼            ▼             ▼               ▼
 Gemini     Chroma DB    sentence-       doc loaders
 (answers)  (vectors)    transformers    (pdf/docx/md/txt)
```

Every backend concern is in its own small module under `app/` — see the
**Project structure** section below. Each file has a header comment explaining
its job, written for a beginner to read top-to-bottom.

---

## 🚀 Quick start

```bash
# 1) Install uv (one time)
pip install uv

# 2) Create env + install deps
uv venv --python 3.11
uv pip install -r requirements.txt

# 3) Add your Gemini key
copy .env.example .env       # then edit GOOGLE_API_KEY
                            # (macOS/Linux: cp .env.example .env)

# 4) (Optional) drop notes into /pdf

# 5) Run
uv run uvicorn app.main:app --reload
#   open http://localhost:8000
```

First launch downloads the embeddings model (~90 MB) and indexes your notes.

> Need a free API key? → https://aistudio.google.com/app/apikey

---

## 📁 Project structure

```
RAG_STUDY_CHATBOT/
├── app/
│   ├── main.py                # FastAPI app: CORS, static, startup
│   ├── api/
│   │   ├── routes.py          # /chat /chat/stream /upload /ingest /sources /health
│   │   └── schemas.py         # pydantic request/response models
│   ├── core/
│   │   ├── config.py          # all settings from .env
│   │   ├── logging.py         # loguru setup
│   │   ├── prompts.py         # ALL LLM prompts (incl. study-only system prompt)
│   │   ├── security.py        # upload validation, magic bytes, filename sanitising
│   │   └── keepalive.py       # anti-sleep ping for Render free tier
│   └── rag/
│       ├── graph.py           # LangGraph: the full pipeline + routing
│       ├── state.py           # GraphState typed dict
│       ├── llm.py             # Gemini chat model
│       ├── embeddings.py      # sentence-transformers (local)
│       ├── vectorstore.py     # Chroma wrapper
│       ├── loader.py          # pdf/docx/md/txt loaders
│       ├── splitter.py        # recursive text splitter
│       ├── ingest.py          # documents → chunks → vector store
│       └── nodes/             # one file per graph node
│           ├── rewrite.py  classify.py  retrieve.py
│           ├── grade.py    generate.py  refuse.py
├── static/                    # frontend (no build step)
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
├── pdf/                       # <-- put your default notes here
├── data/                      # chroma_db + uploads (git-ignored)
├── tests/                     # pytest: security + splitter
├── Dockerfile                 # production image
├── render.yaml                # Render one-click deploy
├── requirements.txt · pyproject.toml · .env.example
├── DEPLOYMENT.md              # full deploy + free-tier trade-offs
└── README.md
```

---

## 🛡️ How "study-only" is enforced (defense in depth)

1. **Rule-based pre-filter** (`nodes/classify.py`) — instantly refuses obvious
   non-study prompts (creative writing, "ignore instructions", role-play…)
   without any API call.
2. **Intent classifier** — a tiny LLM call returns `STUDY` vs `OFFTOPIC`.
   Off-topic → polite refusal, no retrieval.
3. **Document relevance grader** — even for study questions, retrieved chunks
   that don't actually relate are dropped. If nothing remains, the bot says
   "I don't have that in your notes" instead of inventing an answer.
4. **System-prompt lockdown** (`core/prompts.py`) — the generation prompt
   forbids using outside knowledge and instructs the model to refuse.

A determined prompt-injection attempt will still get the canned refusal
message because steps 3 + 4 hold independent of the question's phrasing.

---

## 🌐 Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the full guide.

**TL;DR — Render free tier:**
1. Push to GitHub.
2. Render → New → Blueprint (reads `render.yaml`).
3. Set `GOOGLE_API_KEY` as a secret. Deploy. Done.

Honest free-tier note: Render sleeps after ~15 min idle and has an ephemeral
filesystem (uploaded notes are wiped on restart). The app auto-re-ingests the
`/pdf` folder on every boot so the default knowledge base always returns; a
~$1/mo disk keeps user uploads permanent. Full details in DEPLOYMENT.md.

---

## 🧪 Tests

```bash
uv run pytest
```

Covers the upload security layer and the text splitter (no API keys needed).

---

## 📜 License

MIT — free to use, modify, and share. Be a good citizen with your API key.
"# FikarYaar" 
#   F i k a r Y a a r  
 #   F i k a r Y a a r  
 