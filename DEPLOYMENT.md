# فکریار Deployment Guide — 100% Free, No Credit Card

| Platform | Free Tier | No Card? | Best For |
|----------|-----------|----------|----------|
| **Render** | 750 hrs/mo, 512 MB RAM | ✅ Yes | **Primary — simplest, FastAPI native** |
| **SnapDeploy** | 4 containers, 512 MB RAM each | ✅ Yes | Docker-native, full control |
| **PythonAnywhere** | 1 web app, always-on | ✅ Yes | Beginner-friendly (but no ASGI) |

---

## 🏆 Option 1: Render (Recommended)

### Why Render?
- **No credit card required** — sign up with GitHub/Google
- FastAPI works natively via `requirements.txt` — no Docker needed
- Auto-deploys from GitHub on every push
- Auto HTTPS, custom domains

### Step-by-Step

#### 1. Push to GitHub
```bash
git remote add origin https://github.com/ayan-2007/FikarYaar.git
git push -u origin main
```

#### 2. Create Render Web Service
1. Go to [dashboard.render.com](https://dashboard.render.com)
2. **New** → **Web Service** → Connect your GitHub repo
3. Settings:
   - **Name**: `fikaryaar`
   - **Region**: Frankfurt or Oregon
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: **Free**

#### 3. Add Environment Variables
In Render dashboard → **Environment** tab:
```
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

#### 4. Add Persistent Disk (for Chroma DB)
1. Settings → **Disks** → **Add Disk**
2. Name: `chroma-data`
3. Mount Path: `/app/data/chroma_db`
4. Size: `1 GB`

#### 5. Deploy
Click **Create Web Service**. First deploy takes 2-3 min.

#### 6. Open
`https://fikaryaar.onrender.com`

> **⚠️ Free tier sleeps after 15 min idle.** Cold start ~30s. The app auto-rebuilds its vector DB from bundled PDFs on cold start.

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
- [ ] App loads at your URL
- [ ] Upload a PDF → appears in Knowledge Base
- [ ] Ask a question → cited answer with streaming
- [ ] Quiz feature works
- [ ] Agent switching (Ustad ↔ Muhaqqiq) works

**Happy deploying!** 🎓
