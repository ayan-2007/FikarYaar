# Vercel Migration — What Changed

This project was originally built for long-running servers (Docker, Render, SnapDeploy) with local disk access. Vercel is serverless — each request runs in an isolated function with no persistent filesystem and a 60s execution limit (Pro tier).

## Files Changed

### `app/core/config.py`
- Added `embeddings_provider` (default `"local"`) — switch to `"google"` for serverless
- Added `google_api_key` for Google's free embeddings API
- Added `vector_store` (default `"chroma"`) — switch to `"pinecone"` for serverless
- Added `pinecone_api_key`, `pinecone_index_name`, `pinecone_cloud`, `pinecone_region`

### `app/rag/embeddings.py`
- Now dispatches to `_get_google_embeddings()` or `_get_local_embeddings()` based on `EMBEDDINGS_PROVIDER`
- Google mode uses `models/embedding-001` (free tier, 100 req/s, no local model download)
- Local mode unchanged — still uses FastEmbed with sentence-transformers

### `app/rag/vectorstore.py` (major refactor)
- Completely rewritten as a provider-agnostic abstraction
- `_init_chroma()` — existing Chroma logic, unchanged behavior
- **New** `_init_pinecone()` — connects to Pinecone cloud index via `PINECONE_API_KEY`
- `collection_count()`, `delete_by_source()`, `list_sources()` now dispatch to correct backend
- `retrieve_with_threshold()` — on Pinecone skips distance filtering (cosine similarity, different semantics)
- `similarity_search_with_scores()` — on Pinecone returns cosine similarity (higher=better), on Chroma returns L2 distance (lower=better)
- **Breaking**: Chroma uses L2 distance threshold (≤1.5 filter), Pinecone returns all candidates unfiltered and relies on the LLM grader node for relevance

### `app/main.py`
- Detects Vercel via `VERCEL` env var (auto-set in `api/index.py`)
- Skips auto-ingest on Vercel (no persistent Chroma to rebuild)
- Skips keep-alive on Vercel (serverless has no idle sleep)
- Startup embedding warm-up still runs (first cold-start is slow, subsequent warm starts are fast)

### New Files

| File | Purpose |
|------|---------|
| `api/index.py` | Vercel entry point — imports FastAPI app, sets `VERCEL=1` |
| `vercel.json` | Vercel config — routes `/api/*` to function, `/*` to `static/`, 60s max duration |
| `requirements-vercel.txt` | Slimmed deps — no Chroma, no FastEmbed, adds Pinecone |

## What Gets Sacrificed on Vercel

1. **Local Chroma DB** → replaced by **Pinecone** (free tier: 1 index, 100K vectors). You need a `PINECONE_API_KEY`.

2. **Local embeddings model** (~90MB sentence-transformers) → replaced by **Google Generative AI embeddings** (`models/embedding-001`, free tier 100 req/s). You need a `GOOGLE_API_KEY`.

3. **Auto-ingest on startup** → disabled. On Vercel you must call `POST /api/ingest` to populate the vector store manually, or pre-seed your Pinecone index before deploying.

4. **Keep-alive** → disabled (meaningless in serverless).

5. **Upload storage** — `data/uploads/` writes to `/tmp` which is ephemeral (lives per-request). Uploaded files are ingested into Pinecone immediately via `POST /api/upload`, so the original file is lost after the request but the vectors persist in the cloud.

## What Stays the Same

- All 5 agents: Ustad, Muhaqqiq, Imtehaan, Darban, Mehakkim
- SSE streaming responses
- LangGraph RAG pipeline (rewrite → classify → retrieve → grade → generate)
- Document loaders (PDF, DOCX, PPTX, MD, TXT)
- Quiz engine (Imtehaan)
- Frontend (vanilla HTML/CSS/JS served from `static/`)
- All existing environment variables still work for non-Vercel deploys

## Vercel Environment Variables

```
# Required
GROQ_API_KEY=gsk_your_key           # or GOOGLE_API_KEY for Gemini LLM
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=fikaryaar
EMBEDDINGS_PROVIDER=google
VECTOR_STORE=pinecone

# Optional
GOOGLE_API_KEY=your_google_key       # if using Gemini for embeddings
GROQ_MODEL=llama-3.1-8b-instant
TOP_K=5
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

## How to Keep Running Locally (Unchanged)

```
pip install -e ".[local]"   # includes chromadb + fastembed
uvicorn app.main:app --reload --port 8000
```

The defaults (`VECTOR_STORE=chroma`, `EMBEDDINGS_PROVIDER=local`) mean zero config needed for local dev.

## Deploying to Vercel

```bash
# 1. Create Pinecone index (from their dashboard or CLI)
pinecone create-index --name fikaryaar --dimension 768 --metric cosine

# 2. Deploy
vercel --prod \
  -e GROQ_API_KEY=gsk_... \
  -e PINECONE_API_KEY=... \
  -e PINECONE_INDEX_NAME=fikaryaar \
  -e EMBEDDINGS_PROVIDER=google \
  -e VECTOR_STORE=pinecone

# 3. Seed notes (one-time)
curl -X POST https://your-app.vercel.app/api/ingest
```
