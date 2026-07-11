# Deployment Guide

This guide walks you through running **RAG Study Chatbot** locally, then
deploying it for free (Render), and the honest trade-offs of each option.

---

## 0. Prerequisites

- A Google Gemini API key (free) → https://aistudio.google.com/app/apikey
- Python 3.11 or 3.12 (3.13/3.14 may lack some wheels)
- [`uv`](https://docs.astral.sh/uv/) installed
- Git + a GitHub account (for deployment)

---

## 1. Run locally

```bash
# 1. Install uv if you don't have it
pip install uv

# 2. Create the venv + install deps (uv handles Python version too)
uv venv --python 3.11
uv pip install -r requirements.txt      # or: uv sync (uses pyproject.toml)

# 3. Configure secrets
copy .env.example .env                  # Windows
# cp .env.example .env                  # macOS/Linux
#   -> open .env and paste your GOOGLE_API_KEY

# 4. (Optional) drop a couple of PDFs/DOCX/MD files into /pdf

# 5. Run
uv run uvicorn app.main:app --reload
#   open http://localhost:8000
```

The first run downloads the embeddings model (~90 MB) and ingests everything
in `/pdf`. Subsequent boots are fast.

---

## 2. Deploy to Render (free tier) — recommended

Render runs Docker images and gives a free web service. Steps:

1. **Push the project to GitHub.**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **On Render:**
   - Dashboard → **New** → **Blueprint**
   - Pick your GitHub repo. Render reads `render.yaml`.
   - Under **Environment**, set the secret `GOOGLE_API_KEY` (paste your key).
   - Click **Apply**. Build takes ~5–8 min (it pre-downloads the model).

3. **Open the deployed URL.** Done — you now have a public StudyBuddy.

### Free-tier limits (be aware)

| Limit | Effect |
|---|---|
| Service **sleeps after ~15 min** idle | First request after sleep takes ~30–50 s to wake |
| **Ephemeral filesystem** | Uploaded user notes are **wiped on restart/deploy** |
| 750 free hours/month, then sleep | Fine for personal study use |

**Mitigations already built in:**
- On every boot the app **re-ingests `/pdf`**, so the bundled knowledge base
  always comes back automatically.
- Set `KEEP_ALIVE_ENABLED=true` (already set in render.yaml) so the app pings
  itself every 10 min and stays warm.

### Keep user uploads permanently (optional, ~$1/mo)

Attach a **Disk** (Render's persistent volume):

1. Upgrade the service to a **Starter** plan ($7/mo — required for disks).
2. In the service settings, add a **Disk**:
   - Name: `studybot-data`
   - Mount path: `/app/data`
   - Size: 1 GB
3. Also move `/pdf` onto the disk if you want bundled notes to be editable
   without redeploying.

After this, user uploads in `data/uploads` survive restarts.

---

## 3. Alternative free hosts

| Host | Notes |
|---|---|
| **Fly.io** | Free allowance, supports Docker + persistent volumes. Use `Dockerfile`. `fly deploy`. |
| **Railway** | Free trial credits, then $5/mo. Reads `Dockerfile` directly. |
| **Koyeb** | Free tier, Docker support. |
| **Hugging Face Spaces** | Free, but file system is ephemeral; good for demos. |

The Dockerfile in this repo works on any of them. Only the env vars differ.

> **Vercel note:** Vercel only hosts static/serverless frontends and has a
> 10-second function timeout — not suitable for a heavy Python RAG backend
> with local model inference. Use Render/Fly instead, as chosen.

---

## 4. Production hardening checklist

Before sharing publicly, review:

- [x] `GOOGLE_API_KEY` is a Render **secret**, never in git.
- [x] Upload endpoint validates file types + sizes + magic bytes.
- [x] Study-only guardrail (intent classify → refuse off-topic).
- [x] Model is instructed (system prompt) to refuse outside scope.
- [x] CORS locked to known origins.
- [ ] Consider a rate limiter (e.g. `slowapi`) if abuse is observed.
- [ ] Rotate the API key if it leaks.

---

## 5. Troubleshooting

**"API key missing" in the UI** → set `GOOGLE_API_KEY` in Render env and redeploy.

**First answer is slow (30+ s)** → embeddings model is still downloading, or
the service just woke from sleep. Subsequent answers are fast.

**"No relevant notes found"** → you haven't uploaded anything and `/pdf` is
empty. Upload notes via the UI or drop files in `/pdf` and redeploy.

**Out of memory on Render free (512 MB)** → the MiniLM embeddings + Chroma
fit comfortably; if you switch to a bigger embeddings model you may need a
paid plan with more RAM.
