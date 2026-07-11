/* ============================================================
   فکریار (Fikryar) — Study companion (frontend)
   Enhanced version with:
     - view router (home / chat)
     - canvas particle background (neural pathways)
     - floating geometric shapes
     - hero typer animation
     - SSE streaming chat (source-cited)
     - knowledge-base upload + sources
     - mobile bottom nav + sidebar drawer
     - theme toggle (dark/light)
     - stats tracking
     - scroll animations
   ============================================================ */

const API = "/api";

/* ---------- tiny helpers ---------- */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const el = (tag, cls) => { const e = document.createElement(tag); if (cls) e.className = cls; return e; };
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

/* ---------- state ---------- */
const state = {
  view: "home",
  history: [],
  streaming: false,
  questionsAsked: 0,
  theme: localStorage.getItem("fikryar_theme") || "dark"
};

/* ============================================================
   ENTRANCE — the spark that catches, once per session
   ============================================================ */
(function entrance() {
  const node = document.getElementById("entrance");
  if (!node) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const seen = sessionStorage.getItem("fikryar_entrance_seen");

  if (reduce || seen) {
    node.classList.add("gone");
    return;
  }
  sessionStorage.setItem("fikryar_entrance_seen", "1");

  let closed = false;
  function close() {
    if (closed) return;
    closed = true;
    node.classList.add("leaving");
    setTimeout(() => node.classList.add("gone"), 650);
  }
  node.addEventListener("click", close);
  window.addEventListener("keydown", close, { once: true });
  // full sequence runs ~3.1s if the user doesn't skip it
  setTimeout(close, 3100);
})();

/* ============================================================
   THEME TOGGLE
   ============================================================ */
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("fikryar_theme", theme);
  $("#themeToggle").textContent = theme === "dark" ? "☀" : "🌙";
}
applyTheme(state.theme);

/* ============================================================
   TOAST
   ============================================================ */
let toastTimer;
function toast(msg, type = "") {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show " + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.className = "toast"), 3000);
}

/* ============================================================
   VIEW ROUTER
   ============================================================ */
const TITLES = { home: "Home", chat: "Chat" };

function go(view) {
  state.view = view;
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${view}`));
  $$(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  $$(".bn-item").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  $("#topbarTitle").textContent = TITLES[view] || cap(view);
  $("#sidebar").classList.remove("open");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

$$("[data-view]").forEach((b) => b.addEventListener("click", () => go(b.dataset.view)));
$$("[data-go]").forEach((b) => b.addEventListener("click", () => go(b.dataset.go)));

/* ============================================================
   SIDEBAR DRAWER (mobile)
   ============================================================ */
$("#hamburger").addEventListener("click", () => $("#sidebar").classList.toggle("open"));

/* ============================================================
   THEME TOGGLE
   ============================================================ */
$("#themeToggle").addEventListener("click", () => {
  state.theme = state.theme === "dark" ? "light" : "dark";
  applyTheme(state.theme);
});

/* ============================================================
   FLOATING SHAPES GENERATOR
   ============================================================ */
function createFloatingShapes() {
  const container = $("#floatingShapes");
  if (!container) return;
  const count = window.innerWidth < 700 ? 4 : 6;
  for (let i = 0; i < count; i++) {
    const shape = document.createElement("div");
    shape.className = "floating-shape";
    const size = 40 + Math.random() * 100;
    shape.style.width = size + "px";
    shape.style.height = size + "px";
    shape.style.top = Math.random() * 90 + "%";
    shape.style.left = Math.random() * 90 + "%";
    shape.style.animationDelay = Math.random() * 5 + "s";
    shape.style.animationDuration = 15 + Math.random() * 15 + "s";
    shape.style.borderRadius = `${Math.random() * 50}% ${Math.random() * 50}% ${Math.random() * 50}% ${Math.random() * 50}% / ${Math.random() * 50}% ${Math.random() * 50}% ${Math.random() * 50}% ${Math.random() * 50}%`;
    container.appendChild(shape);
  }
}
createFloatingShapes();

/* ============================================================
   HERO TYPER
   ============================================================ */
const TYPER_WORDS = ["Ask.", "Learn.", "Understand.", "Grow.", "Think Better.", "Discover."];
let twi = 0, twc = 0, twDel = false;
function tickTyper() {
  const node = $("#typer");
  if (!node) return;
  const word = TYPER_WORDS[twi];
  if (twDel) {
    twc--; node.textContent = word.slice(0, twc);
    if (twc === 0) { twDel = false; twi = (twi + 1) % TYPER_WORDS.length; setTimeout(tickTyper, 350); return; }
    setTimeout(tickTyper, 45);
  } else {
    twc++; node.textContent = word.slice(0, twc);
    if (twc === word.length) { twDel = true; setTimeout(tickTyper, 1500); return; }
    setTimeout(tickTyper, 90);
  }
}
tickTyper();

/* ============================================================
   CANVAS PARTICLE BACKGROUND (neural pathways)
   ============================================================ */
(function bg() {
  const canvas = $("#bg-canvas");
  const ctx = canvas.getContext("2d");
  let w, h, particles, raf;
  const COUNT = () => (window.innerWidth < 700 ? 36 : 70);
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function resize() {
    w = canvas.width = window.innerWidth * devicePixelRatio;
    h = canvas.height = window.innerHeight * devicePixelRatio;
    canvas.style.width = window.innerWidth + "px";
    canvas.style.height = window.innerHeight + "px";
  }
  function spawn() {
    particles = [];
    for (let i = 0; i < COUNT(); i++) {
      particles.push({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.25 * devicePixelRatio,
        vy: (Math.random() - 0.5) * 0.25 * devicePixelRatio,
        r: (Math.random() * 1.6 + 0.6) * devicePixelRatio,
      });
    }
  }
  function step() {
    ctx.clearRect(0, 0, w, h);
    const linkDist = 130 * devicePixelRatio;
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(255,179,71,0.55)";
      ctx.fill();
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j];
        const dx = p.x - q.x, dy = p.y - q.y;
        const d = Math.hypot(dx, dy);
        if (d < linkDist) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = `rgba(255,122,26,${0.16 * (1 - d / linkDist)})`;
          ctx.lineWidth = devicePixelRatio * 0.6;
          ctx.stroke();
        }
      }
    }
    raf = requestAnimationFrame(step);
  }
  resize(); spawn();
  if (!reduce) step(); else { ctx.clearRect(0, 0, w, h); }
  let rt;
  window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { resize(); spawn(); }, 200); });
  // pause when tab hidden (battery friendly)
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) cancelAnimationFrame(raf);
    else if (!reduce) step();
  });
})();

/* ============================================================
   MARKDOWN (tiny safe renderer)
   ============================================================ */
function escapeHtml(s) {
  return s.replace(/&/g, "&").replace(/</g, "<").replace(/>/g, ">");
}
function renderMarkdown(text) {
  let h = escapeHtml(text);
  h = h.replace(/```([\s\S]*?)```/g, (_, c) => `<pre><code>${c.trim()}</code></pre>`);
  h = h.replace(/`([^`]+)`/g, "<code>$1</code>");
  h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  h = h.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  h = h.replace(/^### (.+)$/gm, "<p><strong>$1</strong></p>");
  h = h.replace(/^## (.+)$/gm, "<p><strong>$1</strong></p>");
  h = h.replace(/^# (.+)$/gm, "<p><strong>$1</strong></p>");
  h = h.replace(/^[\-\*] (.+)$/gm, "<li>$1</li>");
  h = h.replace(/(<li>[\s\S]+?<\/li>)/g, "<ul>$1</ul>");
  h = h.replace(/^\d+\. (.+)$/gm, "<li>$1</li>");
  h = h.split(/\n{2,}/).map((b) =>
    b.startsWith("<ul>") || b.startsWith("<pre>") ? b : `<p>${b.replace(/\n/g, "<br>")}</p>`).join("");
  return h;
}

/* ============================================================
   CHAT — message rendering
   ============================================================ */
function addMessage(role, content) {
  $("#welcome").style.display = "none";
  const wrap = el("div", `msg ${role}`);
  const avatar = el("div", "avatar");
  avatar.textContent = role === "user" ? "🧑" : "✦";
  const bubble = el("div", "bubble");
  bubble.innerHTML = role === "user" ? escapeHtml(content).replace(/\n/g, "<br>") : renderMarkdown(content);
  wrap.append(avatar, bubble);
  $("#messages").append(wrap);
  $("#chat").scrollTop = $("#chat").scrollHeight;
  return bubble;
}
function addTyping() {
  $("#welcome").style.display = "none";
  const wrap = el("div", "msg bot");
  const avatar = el("div", "avatar"); avatar.textContent = "✦";
  const bubble = el("div", "bubble");
  const typing = el("div", "typing"); typing.innerHTML = "<span></span><span></span><span></span>";
  bubble.append(typing);
  wrap.append(avatar, bubble);
  $("#messages").append(wrap);
  $("#chat").scrollTop = $("#chat").scrollHeight;
  return { wrap, bubble };
}
function attachSources(bubble, sources) {
  if (!sources || !sources.length) return;
  const tag = el("div", "sources-tag");
  sources.forEach((s) => {
    const chip = el("span", "src-chip");
    if (s.snippet) chip.dataset.tooltip = s.snippet;
    chip.innerHTML = `<span class="badge">${(s.type || "?").toUpperCase()}</span> ${escapeHtml(s.name)}`;
    tag.append(chip);
  });
  bubble.append(tag);
}

/* ============================================================
   CHAT — submit (SSE streaming)
   ============================================================ */
const ta = $("#question");
ta.addEventListener("input", () => {
  ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  $("#sendBtn").disabled = ta.value.trim() === "";
});
ta.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#composer").requestSubmit(); }
});

$("#composer").addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = ta.value.trim();
  if (!question || state.streaming) return;

  addMessage("user", question);
  state.history.push({ role: "user", content: question });
  ta.value = ""; ta.style.height = "auto"; $("#sendBtn").disabled = true;
  state.streaming = true; $("#sendBtn").style.opacity = "0.5";

  const { wrap, bubble } = addTyping();
  let answerText = "";
  state.questionsAsked++;
  updateStats();

  try {
    const resp = await fetch(`${API}/chat/stream`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history: state.history.slice(-6, -1) }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    let buffer = "", sourcesShown = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += dec.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop();
      for (const frame of frames) {
        const lines = frame.split("\n");
        let evt = "message", data = "";
        for (const ln of lines) {
          if (ln.startsWith("event:")) evt = ln.slice(6).trim();
          else if (ln.startsWith("data:")) data += ln.slice(5).trim();
        }
        if (!data) continue;
        let payload = {}; try { payload = JSON.parse(data); } catch { continue; }

        if (evt === "sources") {
          if (!sourcesShown) { bubble.innerHTML = ""; sourcesShown = true; }
          attachSources(bubble, payload.sources);
        } else if (evt === "token") {
          if (!sourcesShown) { bubble.innerHTML = ""; sourcesShown = true; }
          answerText += payload.token;
          bubble.innerHTML = renderMarkdown(answerText);
          $("#chat").scrollTop = $("#chat").scrollHeight;
        } else if (evt === "done") {
          if (!answerText) bubble.innerHTML = "<em>(no answer)</em>";
        }
      }
    }
    state.history.push({ role: "assistant", content: answerText });
  } catch (err) {
    bubble.innerHTML = `<p>⚠️ Couldn't reach the server (${escapeHtml(err.message)}). Is the backend running?</p>`;
  } finally {
    state.streaming = false;
    $("#sendBtn").style.opacity = "1";
    $("#sendBtn").disabled = ta.value.trim() === "";
  }
});

/* suggestion chips → fill composer and send */
function wireChips() {
  $$(".chip").forEach((b) => {
    if (b.dataset.wired) return;
    b.dataset.wired = "1";
    b.addEventListener("click", () => {
      if (state.view !== "chat") go("chat");
      ta.value = b.dataset.q; ta.dispatchEvent(new Event("input"));
      $("#composer").requestSubmit();
    });
  });
}
wireChips();

/* ============================================================
   UPLOAD
   ============================================================ */
$("#fileInput").addEventListener("change", async (e) => {
  const files = [...e.target.files]; if (!files.length) return;
  await uploadFiles(files); e.target.value = "";
});
async function uploadFiles(files) {
  let prog = $(".upload-progress");
  if (!prog) { prog = el("div", "upload-progress"); document.body.append(prog); }
  prog.innerHTML = `<div class="upload-text">📤 Uploading ${files.length} file(s)…</div><div class="bar"><div class="bar-fill"></div></div>`;
  prog.classList.add("active");
  const fd = new FormData(); files.forEach((f) => fd.append("files", f));
  try {
    const resp = await fetch(`${API}/upload`, { method: "POST", body: fd });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);
    prog.querySelector(".bar-fill").style.width = "100%";
    setTimeout(() => prog.classList.remove("active"), 800);
    toast(`✅ Added ${data.chunks_added} chunks from ${data.files.length} file(s)`, "success");
    await refreshSources(); await refreshStats();
  } catch (err) {
    prog.classList.remove("active");
    toast(`❌ Upload failed: ${err.message}`, "error");
  }
}
["dragover"].forEach((ev) => document.addEventListener(ev, (e) => e.preventDefault()));
document.addEventListener("drop", async (e) => {
  e.preventDefault();
  const files = [...(e.dataTransfer?.files || [])].filter((f) => /\.(pdf|docx|pptx|md|txt|markdown)$/i.test(f.name));
  if (files.length) await uploadFiles(files);
});

/* ============================================================
   SOURCES + HEALTH (knowledge base)
   ============================================================ */
async function refreshSources() {
  try {
    const r = await fetch(`${API}/sources`); const d = await r.json();
    const list = $("#sourceList"); list.innerHTML = "";
    if (!d.sources || !d.sources.length) { list.innerHTML = '<li class="source-empty">No notes uploaded yet.</li>'; return; }
    d.sources.forEach((s) => {
      const li = el("li");
      li.innerHTML = `<span class="ftype">${(s.type || "?").toUpperCase()}</span><span class="fname" title="${s.name}">${s.name}</span>`;
      const del = el("button", "del-btn"); del.textContent = "✕"; del.title = "Remove";
      del.addEventListener("click", async () => {
        if (!confirm(`Remove "${s.name}" from the knowledge base?`)) return;
        const rr = await fetch(`${API}/sources/${encodeURIComponent(s.name)}`, { method: "DELETE" });
        if (rr.ok) { toast("Removed", "success"); refreshSources(); refreshStats(); }
      });
      li.append(del); list.append(li);
    });
  } catch { /* silent */ }
}
async function refreshStats() {
  try {
    const r = await fetch(`${API}/health`); const d = await r.json();
    $("#chunkCount").textContent = d.chunks.toLocaleString();
    $("#sourceCount").textContent = d.sources;
    updateStats(d.chunks, d.sources);
    const dot = $("#statusDot"), txt = $("#statusText");
    if (d.llm_configured && d.chunks > 0) { dot.className = "dot ok"; txt.textContent = "Ready"; }
    else if (!d.llm_configured) { dot.className = "dot err"; txt.textContent = "API key missing"; }
    else { dot.className = "dot"; txt.textContent = "No notes yet"; }
  } catch {
    $("#statusDot").className = "dot err"; $("#statusText").textContent = "Offline";
  }
}
function updateStats(chunks, sources) {
  if (chunks !== undefined) $("#statChunks").textContent = chunks.toLocaleString();
  if (sources !== undefined) $("#statSources").textContent = sources;
  $("#statQuestions").textContent = state.questionsAsked;
}
$("#refreshSources").addEventListener("click", () => { refreshSources(); refreshStats(); });

/* ============================================================
   ABOUT MODAL
   ============================================================ */
$("#aboutLink").addEventListener("click", (e) => { e.preventDefault(); $("#aboutModal").classList.add("active"); });
$("#modalClose").addEventListener("click", () => $("#aboutModal").classList.remove("active"));
$("#aboutModal").addEventListener("click", (e) => { if (e.target.id === "aboutModal") $("#aboutModal").classList.remove("active"); });

/* ============================================================
   SCROLL ANIMATIONS (IntersectionObserver)
   ============================================================ */
function initScrollAnimations() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = "running";
        entry.target.classList.add("in-view");
      }
    });
  }, { threshold: 0.1, rootMargin: "0px 0px -50px 0px" });

  $$(".feature-card, .path-step, .stat-item, .test-chips .chip").forEach((el, i) => {
    el.style.animationPlayState = "paused";
    el.style.animationDelay = (i * 0.05) + "s";
    observer.observe(el);
  });
}

/* ============================================================
   PARALLAX EFFECT ON HERO
   ============================================================ */
function initParallax() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const hero = document.querySelector(".hero");
  if (!hero) return;
  window.addEventListener("scroll", () => {
    const scrolled = window.scrollY;
    const rate = scrolled * -0.3;
    hero.style.transform = `translateY(${rate}px)`;
  }, { passive: true });
}

/* ============================================================
   INIT
   ============================================================ */
refreshStats(); refreshSources();
setInterval(refreshStats, 30000);
go("home");

// Initialize enhancements after DOM is ready
setTimeout(() => {
  initScrollAnimations();
  initParallax();
}, 100);

/* Expose for debugging */
window.Fikryar = { state, go, toast, refreshSources, refreshStats };