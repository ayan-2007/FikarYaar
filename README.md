# فکریار (Fikaryaar) — RAG Study Assistant

<div align="center">

# فکریار (FikarYaar)
### RAG-Powered Study & Deep Research Assistant

*Upload your notes. Ask anything. Get grounded, cited, cyberpunk-flavored answers.*

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-RAG%20Pipeline-1C3C3C)](https://www.langchain.com/)
[![Groq](https://img.shields.io/badge/Groq-LLM%20Inference-F55036)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 Overview

**FikarYaar** is a production-ready, multi-agent Retrieval-Augmented Generation (RAG) platform built for students and researchers. Upload your notes — PDF, DOCX, PPTX, Markdown, or plain text — and get grounded, footnoted answers, deep research paper breakdowns, and adaptive quizzes, all wrapped in a cyberpunk-academic interface with real-time streaming responses.

No frameworks. No build step. Just a fast FastAPI backend, a local embedding model, and five specialized AI agents working together.

---

## 🤖 Meet the Agents

FikarYaar isn't a single chatbot — it's a coordinated team of five specialized agents, each with a distinct job:

| Agent | Role | What It Does |
|---|---|---|
| 🎓 **Ustad** (استاد) — Tutor | Source-grounded Q&A | Strict, footnoted answers from your notes with analogies and key takeaways. Falls back to general knowledge when a topic isn't covered. |
| 🔬 **Muhaqqiq** (محقق) — Researcher | Deep paper analysis | Breaks papers into Delta, Core Intuition, Evidence Anchor, and Blindspots. Cross-examines hypotheses with confidence scores and synthesizes multiple papers into a literature matrix. |
| 📝 **Imtehaan** (امتحان) — Examiner | Adaptive quizzing | 5-level quizzes (Easy → Extreme), real-time scoring out of 10, missed-concept analysis, and an Urdu encouragement grade report. |
| 🚪 **Darban** (دربان) — Doorkeeper | Guardrails | Classifies intent and gracefully rejects off-topic queries. |
| ✅ **Mehakkim** (محکِّم) — Validator | Quality control | Assesses retrieval quality and coverage before an answer is finalized. |

---

## ✨ Key Features

- 📂 Multi-format upload: PDF, DOCX, PPTX, MD, TXT
- 🖱️ Drag-and-drop ingestion with live knowledge base stats
- ⚡ Server-Sent Events (SSE) streaming — tokens appear as they're generated
- 🔄 Instant switching between 5 specialized agent modes
- 🧠 Adaptive quiz engine with real-time grading
- 📑 Structural research paper deconstruction
- 🔍 Hypothesis cross-examination against source papers
- 📚 Multi-document literature synthesis
- 🛡️ Off-topic refusal and guardrails baked in
- 💤 Keep-alive mechanism for free-tier hosting

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, LangChain, LangGraph |
| **Vector Store** | Chroma |
| **LLM** | Groq (`llama-3.1-8b-instant`) via `langchain-groq` |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (local, ~90MB, no API key) |
| **Frontend** | Vanilla HTML5 / CSS3 / JS — no frameworks, no build step |
| **Design** | Deep Obsidian (`#080A10`) & Flame Amber (`#FF6B00`) cyberpunk-academic theme, glassmorphism, custom particle canvas engine |
| **Streaming** | Server-Sent Events (SSE) |

---




## 🧭 How It Works

1. **Upload** your notes via drag-and-drop or the file picker.
2. Notes are **chunked, embedded**, and stored in a Chroma vector database.
3. **Select an agent mode** — Ustad, Muhaqqiq, or Imtehaan.
4. **Ask a question** — the agent retrieves relevant chunks, grounds its answer, and streams the response back with citations.
5. For research papers, get a full **structural breakdown**, cross-examine claims, or synthesize several papers at once.
6. For quizzes, the agent detects the topic, generates **adaptive questions**, evaluates your answers, and produces a grade report.

---

## 📁 Project Structure

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

---



<div align="center">

Made with 🔥 and too much coffee.

</div>
