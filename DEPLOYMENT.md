# 🚀 Fikaryaar Deployment Guide

Deploy your RAG study chatbot for **free** on multiple platforms. This guide covers the three best free-tier options.

---

## 📋 Prerequisites

1. **GitHub account** — for code hosting & CI/CD
2. **Groq API key** — free at [console.groq.com](https://console.groq.com/keys)
3. **Docker Hub / GHCR** — for container images (free)

---

## 🎯 Quick Comparison

| Platform | Free Tier | Sleep? | Best For |
|----------|-----------|--------|----------|
| **Render** | 750 hrs/mo, 512 MB RAM | After 15 min idle | **Primary recommendation** — simplest |
| **Fly.io** | 3 shared-cpu VMs, 160 GB transfer | Never | Docker-native, always-on |
| **Railway** | 500 hrs/mo, $5 credit/mo | Never | Alternative with generous credit |

---

## 🏆 Option 1: Render (Recommended)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fikaryaar.git
git push -u origin main
```

### 2. Create Render Web Service
1. Go to [dashboard.render.com](https://dashboard.render.com)
2. **New** → **Web Service** → Connect your GitHub repo
3. Settings:
   - **Name**: `fikaryaar`
   - **Region**: Oregon (US West) or closest
   - **Branch**: `main`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Plan**: `Free`

### 3. Add Environment Variables
In Render dashboard → **Environment** tab, add:
```
GROQ_API_KEY=gsk_your_groq_key_here
GROQ_MODEL=llama-3.1-8b-instant
KEEP_ALIVE_ENABLED=true
KEEP_ALIVE_URL=https://fikaryaar.onrender.com
```
> **Note**: `KEEP_ALIVE_URL` prevents the free tier from sleeping. Render pings itself every 10 min.

### 4. Add Persistent Disk (for Chroma DB)
1. In service settings → **Disks** → **Add Disk**
2. Name: `chroma-data`
3. Mount Path: `/app/data/chroma_db`
4. Size: `1 GB` (free tier limit)

### 5. Deploy
Click **Create Web Service**. First deploy takes 5-10 min (downloads embeddings model).

### 6. Verify
- Health: `https://fikaryaar.onrender.com/api/health`
- App: `https://fikaryaar.onrender.com`

---

## ✈️ Option 2: Fly.io (Always-On, Docker-Native)

### 1. Install Fly CLI
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh
```

### 2. Login & Launch
```bash
fly auth login
fly launch --name fikaryaar --region ord --dockerfile Dockerfile
```
- Choose **No** for PostgreSQL, Redis
- Select **Free** plan (shared-cpu-1x, 256 MB)

### 3. Set Secrets
```bash
fly secrets set GROQ_API_KEY=gsk_your_key_here
fly secrets set GROQ_MODEL=llama-3.1-8b-instant
```

### 4. Configure Volume (for Chroma persistence)
```bash
fly volumes create chroma_data --region ord --size 1
```
Edit `fly.toml`:
```toml
[mounts]
source = "chroma_data"
destination = "/app/data/chroma_db"
```

### 5. Deploy
```bash
fly deploy
```

### 6. Verify
```bash
fly open
# or visit https://fikaryaar.fly.dev
```

---

## 🚂 Option 3: Railway

### 1. Connect Repo
1. Go to [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub repo**
3. Select your repo

### 2. Configure
- **Dockerfile**: Auto-detected
- **Port**: `8000`
- **Healthcheck**: `/api/health`

### 3. Variables
Add in **Variables** tab:
```
GROQ_API_KEY=gsk_xxx
GROQ_MODEL=llama-3.1-8b-instant
```

### 4. Add Volume
1. **New** → **Volume**
2. Mount path: `/app/data/chroma_db`

### 5. Deploy
Auto-deploys on push to main.

---

## 🔄 CI/CD with GitHub Actions

The `.github/workflows/ci-cd.yml` handles:
1. **Lint & Test** on every push/PR
2. **Build & Push** Docker image to GHCR on merge to main
3. **Auto-deploy** to Render/Fly/Railway (configure secrets)

### Required GitHub Secrets
Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Description |
|--------|-------------|
| `RENDER_DEPLOY_HOOK` | From Render: Settings → Deploy Hook |
| `FLY_API_TOKEN` | `fly tokens create deploy` |
| `FLY_APP_NAME` | Your Fly app name (e.g., `fikaryaar`) |

---

## 🐳 Local Docker Development

### Build & Run
```bash
# Build
docker compose build

# Run with .env
docker compose --env-file .env up -d

# View logs
docker compose logs -f app

# Stop
docker compose down
```

### .env File (create from example)
```bash
cp .env.example .env
# Edit .env with your GROQ_API_KEY
```

---

## 📦 Manual Docker Deploy (Any VPS)

```bash
# On your server
docker pull ghcr.io/yourusername/fikaryaar:latest

docker run -d \
  --name fikaryaar \
  -p 8000:8000 \
  -e GROQ_API_KEY=gsk_xxx \
  -e GROQ_MODEL=llama-3.1-8b-instant \
  -v /path/to/chroma:/app/data/chroma_db \
  -v /path/to/uploads:/app/data/uploads \
  -v /path/to/pdf:/app/pdf:ro \
  --restart unless-stopped \
  ghcr.io/yourusername/fikaryaar:latest
```

Add nginx reverse proxy + SSL (Let's Encrypt) for production.

---

## 🔧 Troubleshooting

### "Embeddings model download fails"
- First run downloads ~90 MB model. Allow 60-120s on cold start.
- Pre-warm: `docker run --rm ghcr.io/... python -c "from app.rag.embeddings import get_embeddings; get_embeddings()"`

### "Chroma DB locked / permission denied"
- Ensure volume mounts have correct ownership: `chown -R 1000:1000 /data/chroma_db`
- In Dockerfile, user is `appuser` (UID 1000)

### "Out of memory on free tier"
- Reduce `TOP_K` to 3-4
- Reduce `RETRIEVAL_CANDIDATE_K` to 10
- Use smaller embedding model: `sentence-transformers/all-MiniLM-L6-v2` (already default)

### "Groq rate limit / 429"
- Free tier: 30 RPM, 6000 TPM
- App uses fallback to Gemini if `GEMINI_API_KEY` also set
- Consider `llama-3.1-8b-instant` (fastest, highest limits)

---

## 📊 Monitoring

| Platform | Logs | Metrics |
|----------|------|---------|
| Render | Dashboard → Logs | Built-in CPU/RAM |
| Fly.io | `fly logs` | `fly dashboard` |
| Railway | Dashboard → Deployments | Built-in |

Health endpoint: `GET /api/health` returns:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "chunks": 1347,
  "sources": 1,
  "llm_configured": true,
  "embeddings_loaded": true
}
```

---

## 💰 Cost Summary (Free Tier)

| Resource | Render | Fly.io | Railway |
|----------|--------|--------|---------|
| Compute | 750 hrs/mo | 3 VMs × 24/7 | 500 hrs/mo + $5 credit |
| RAM | 512 MB | 256 MB / VM | 512 MB |
| Storage | 1 GB disk | 1 GB volume | 1 GB |
| Bandwidth | 100 GB/mo | 160 GB/mo | Included |
| Custom Domain | ✅ Free | ✅ Free | ✅ Free |
| SSL | ✅ Auto | ✅ Auto | ✅ Auto |

---

## ✅ Post-Deploy Checklist

- [ ] Health check returns `status: "ok"`
- [ ] Frontend loads at root URL
- [ ] Upload a PDF → appears in Knowledge Base panel
- [ ] Ask a question → gets cited answer
- [ ] Streaming works (tokens appear progressively)
- [ ] Sources panel shows clickable citations
- [ ] Quiz feature generates questions
- [ ] Custom domain configured (optional)

---

## 📝 Notes

- **Embeddings model** downloads on first run (~90 MB). Subsequent starts are instant.
- **Chroma DB** persists in volume. Survives restarts/redeploys.
- **Groq free tier** is generous. No credit card needed.
- **Keep-alive** (Render) prevents cold starts but uses hours. Disable if not needed: `KEEP_ALIVE_ENABLED=false`
- **Multiple agents**: Ustad (notes Q&A), Muhaqqiq (research), Imtehaan (quiz), Darban (gatekeeper), Mehakkim (grader)

---

**Happy deploying!** 🎓✨