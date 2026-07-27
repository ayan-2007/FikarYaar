# فکریار Deployment Guide — 100% Free, No Credit Card

| Platform | Free Tier | No Card? | Best For |
|----------|-----------|----------|----------|
| **Render** | 750 hrs/mo, 512 MB RAM, 0.1 CPU | ✅ Yes | **Primary — Docker auto-detected** |
| **SnapDeploy** | 4 containers, 512 MB RAM each | ✅ Yes | Docker-native, full control |

---

## 🏆 Option 1: Render (Recommended)

### Why Render?
- **No credit card required** — sign up with GitHub/Google/GitLab
- Auto-detects your `Dockerfile` — just connect repo
- Auto-deploys on every commit to `main`
- Auto HTTPS, custom domains, health checks

### Step-by-Step

#### 1. Push to GitHub
```bash
git remote add origin https://github.com/ayan-2007/FikarYaar.git
git push -u origin main
```

#### 2. Create Render Web Service
1. Go to [dashboard.render.com](https://dashboard.render.com)
2. **New** → **Web Service** → Connect your `ayan-2007/FikarYaar` repo
3. Render auto-fills because it detects your `Dockerfile`:

| Field | Value |
|-------|-------|
| **Name** | `FikarYaar` |
| **Language** | `Docker` (auto-detected) |
| **Branch** | `main` |
| **Region** | `Oregon (US West)` |
| **Instance Type** | **Free** ($0/mo, 512 MB RAM, 0.1 CPU) |
| **Health Check Path** | `/api/health` |
| **Docker Build Context** | `.` (root, default) |
| **Dockerfile Path** | `./Dockerfile` (default) |
| **Auto-Deploy** | `On Commit` (default) |

#### 3. Add Environment Variables
Scroll down to **Environment Variables** and add:

| Key | Value |
|-----|-------|
| `GROQ_API_KEY` | `gsk_your_key_here` |
| `GROQ_MODEL` | `llama-3.1-8b-instant` |

#### 4. Deploy
Click **Deploy Web Service** at the bottom.

First build takes 3-5 minutes (installs Python deps, downloads ~90 MB embedding model, builds Docker image). Subsequent builds use cache and are faster.

#### 5. Open
`https://fikaryaar.onrender.com`

> **⚠️ Free tier spins down after 15 min of inactivity.** Cold start ~30s. The app auto-rebuilds its Chroma vector DB from the bundled PDFs in `pdf/` on every cold start (`app/main.py:83-94`), so no persistent disk is needed.

---

## ⚡ Option 2: SnapDeploy (Docker-Native)

1. Create account at [snapdeploy.dev](https://snapdeploy.dev) — no card
2. Connect GitHub repo
3. It auto-detects Dockerfile, sets port 8000
4. Add `GROQ_API_KEY` as env secret
5. Deploy — container auto-sleeps when idle, wakes on traffic

---

## 🔑 Getting a Groq API Key (Free, No Card)
1. [console.groq.com/keys](https://console.groq.com/keys) — sign in with Google/GitHub
2. **No credit card required**
3. Create key (starts with `gsk_`)

---

## ✅ Post-Deploy Checklist
- [ ] `https://fikaryaar.onrender.com/api/health` returns `{"status": "ok"}`
- [ ] Frontend loads at root URL
- [ ] Upload a PDF → appears in Knowledge Base panel
- [ ] Ask a question → cited answer streams in progressively
- [ ] Quiz feature generates questions and grades answers
- [ ] Agent switching (Ustad ↔ Muhaqqiq) works

**Happy deploying!** 🎓
