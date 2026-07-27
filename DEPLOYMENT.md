# فکریار Deployment Guide — 100% Free, No Credit Card

| Platform | Free Tier | No Card? | Best For |
|----------|-----------|----------|----------|
| **SnapDeploy** | 10 deploys/day, 512 MB RAM, auto-wake | ✅ Yes | **Primary — Docker-native, no card** |
| **FastAPI Cloud** | Hobby plan, 3000 req/mo | ✅ Yes | Built by FastAPI team, serverless |

---

## 🏆 Option 1: SnapDeploy (Recommended)

### Why SnapDeploy?
- **No credit card required** — sign up with GitHub
- Docker-native — your `Dockerfile` works as-is
- Auto-detects Python/FastAPI and port 8000
- Auto-deploys from GitHub on every push
- Free tier: 10 deploys/day, auto-sleep/wake

### Step-by-Step

#### 1. Push to GitHub
```bash
git remote add origin https://github.com/ayan-2007/FikarYaar.git
git push -u origin main
```

#### 2. Create account on SnapDeploy
1. Go to [snapdeploy.dev](https://snapdeploy.dev)
2. Sign in with **GitHub** — no credit card asked
3. Click **Deploy from GitHub**

#### 3. Connect your repo
1. Select `ayan-2007/FikarYaar`
2. SnapDeploy auto-detects:
   - **Framework**: Python/FastAPI
   - **Dockerfile**: detected
   - **Port**: 8000 (auto-set)

#### 4. Add Environment Variables
| Key | Value |
|-----|-------|
| `GROQ_API_KEY` | `gsk_your_key_here` |
| `GROQ_MODEL` | `llama-3.1-8b-instant` |

#### 5. Deploy
Click **Deploy**. First build takes 3-5 minutes (installs deps, downloads ~90 MB embedding model, builds Docker image).

#### 6. Open
`https://fikaryaar.snapdeploy.app`

> **⚠️ Free containers auto-sleep when idle.** Auto-wakes on traffic (10-30s). The app auto-rebuilds its Chroma vector DB from bundled PDFs in `pdf/` on every cold start (`app/main.py:83-94`), so no persistent disk is needed.

---

## ⚡ Option 2: FastAPI Cloud

1. Go to [fastapicloud.com](https://fastapicloud.com)
2. Sign up — **no credit card** (Hobby plan)
3. Connect your GitHub repo
4. Set `GROQ_API_KEY` and `GROQ_MODEL` as env vars
5. Deploy — serverless, pay-per-request, 3000 free requests/mo

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
