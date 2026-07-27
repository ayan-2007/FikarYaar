# فکریار Deployment Guide — 100% Free, No Credit Card Required

Deploy your RAG study chatbot for **free** without ever entering a payment method.

| Platform | Free Tier | No Card? | Persistence | Best For |
|----------|-----------|----------|-------------|----------|
| **Hugging Face Spaces (Docker)** | 2 vCPU, 16 GB RAM, 50 GB bandwidth | ✅ Yes | Auto-rebuilds on restart | **Primary — simplest, no card** |
| **Replit Deployments** | Always-on, limited compute | ✅ Yes | Ephemeral | Quick prototype / dev share |
| **PythonAnywhere** | 512 MB RAM, 1 web app | ✅ Yes | Persistent filesystem | Light usage |

---

## 🏆 Option 1: Hugging Face Spaces (Docker) — Recommended

### Why HF Spaces?
- **No credit card required** — sign up with GitHub or email
- Supports Docker containers natively (your `Dockerfile` works as-is)
- Built-in auto-ingest: the app rebuilds its vector database from bundled PDFs on every cold start

### Step-by-Step

#### 1. Create a Hugging Face account
1. Go to [huggingface.co](https://huggingface.co) and click **Sign Up**
2. Use **GitHub** or email — no credit card asked

#### 2. Create a new Space
1. Click your avatar → **New Space**
2. Fill in:
   - **Space Name**: `fikaryaar`
   - **License**: MIT
   - **Space SDK**: **Docker**
   - **Docker Template**: **Blank**
   - **Space Hardware**: **CPU free** (2 vCPU, 16 GB)
3. Click **Create Space**

#### 3. Upload your code (via Git)
```bash
# Clone your repo
git clone https://github.com/ayan-2007/FikarYaar.git
cd FikarYaar

# Add HF as a remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/fikaryaar

# Push
git push hf main
```

Or upload files directly via the HF Spaces web UI.

#### 4. Set environment variables
In the Space page:
1. **Settings** → **Repository Secrets** → **New secret**
2. Add:
   - `GROQ_API_KEY` = `gsk_your_groq_key_here`
   - `GROQ_MODEL` = `llama-3.1-8b-instant`

#### 5. Wait for build
HF builds the Docker image automatically. First build takes 3-5 minutes (installs dependencies + downloads ~90 MB embedding model). Subsequent builds are faster due to Docker layer caching.

#### 6. Open your app
Your Space URL: `https://YOUR_USERNAME-fikaryaar.hf.space`

### ⚠️ Persistence Note
HF Spaces free tier has **ephemeral storage** — the Chroma vector DB is rebuilt from the bundled PDFs (in `pdf/`) on each restart. User-uploaded files are lost on restart. This is acceptable because:
- Default notes are always available
- Uploads can be re-added after restart
- Upgrade to a paid HF Space ($0.60/hr) for persistent storage

---

## 🧪 Option 2: Replit Deployments

1. Fork the repo to Replit
2. Go to **Deployments** tab
3. Add `GROQ_API_KEY` as a secret
4. Deploy — no credit card needed

---

## 🐍 Option 3: PythonAnywhere

1. Create account at [pythonanywhere.com](https://pythonanywhere.com) — no card
2. Clone repo via Bash console
3. Set up a web app with uvicorn
4. Set `GROQ_API_KEY` in environment variables

---

## 🔑 Getting a Groq API Key (Free, No Card)
1. Go to [console.groq.com/keys](https://console.groq.com/keys)
2. Sign in with Google/GitHub — **no credit card required**
3. Click **Create API Key**
4. Copy the key (starts with `gsk_`)

---

## 📝 Notes
- **Embeddings model** (~90 MB) downloads on first run; cached in Docker layers
- **Auto-ingest**: bundled PDFs in `pdf/` are auto-loaded into Chroma on every cold start
- **Groq free tier**: 30 RPM, 6000 TPM — more than enough for personal use
- **Keep-alive**: HF Spaces don't sleep, so no keep-alive needed
- **Custom domain**: HF Spaces support custom domains on free tier

---

## ✅ Post-Deploy Checklist
- [ ] App loads at your Spaces URL
- [ ] Upload a PDF → appears in Knowledge Base panel
- [ ] Ask a question → get cited answer with streaming
- [ ] Quiz feature generates questions
- [ ] Agent switching (Ustad ↔ Muhaqqiq) works

**Happy deploying!** 🎓✨
