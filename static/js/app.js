const API = "/api";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const mk = (tag, cls) => { const e = document.createElement(tag); if (cls) e.className = cls; return e; };

const state = { view: "home", history: [], streaming: false, agent: "ustad", muhaqqiqMode: "analyze", muhaqqiqSource: "" };

/* ═══ TOAST ════════════════════════════════════════════════ */
let _toastT;
function toast(msg, type = "") {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show " + type;
  clearTimeout(_toastT);
  _toastT = setTimeout(() => (t.className = "toast"), 3200);
}

/* ═══ VIEW ROUTER ══════════════════════════════════════════ */
function go(view) {
  state.view = view;
  $$(".view").forEach(v => v.classList.toggle("active", v.id === `view-${view}`));
  $$(".nav-tab").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  closeMobileMenu();
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (view === "chat") { $("#question").focus(); }
}
$$("[data-view]").forEach(b => b.addEventListener("click", () => go(b.dataset.view)));
$$("[data-go]").forEach(b => b.addEventListener("click", () => go(b.dataset.go)));

/* ═══ MOBILE MENU ══════════════════════════════════════════ */
const mobileMenu = $("#mobileMenu");
function closeMobileMenu() { mobileMenu.classList.remove("open"); }
$("#hamburger").addEventListener("click", () => mobileMenu.classList.toggle("open"));

/* ═══ NAV SCROLL EFFECT ════════════════════════════════════ */
const nav = $("#nav");
window.addEventListener("scroll", () => {
  nav.classList.toggle("scrolled", window.scrollY > 20);
}, { passive: true });

/* ═══ SCROLL TO HOW ════════════════════════════════════════ */
$("#scrollHow")?.addEventListener("click", () => {
  $("#howSection")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

/* ═══ KB PANEL ═════════════════════════════════════════════ */
const kbPanel = $("#kbPanel"), kbBackdrop = $("#kbBackdrop");
function openKB()  { kbPanel.classList.add("open"); kbBackdrop.classList.add("open"); }
function closeKB() { kbPanel.classList.remove("open"); kbBackdrop.classList.remove("open"); }
$("#kbToggle").addEventListener("click", openKB);
$("#kbClose").addEventListener("click", closeKB);
kbBackdrop.addEventListener("click", closeKB);

/* ═══ CANVAS PARTICLE FIELD ════════════════════════════════ */
(function particles() {
  const c = $("#canvas"), ctx = c.getContext("2d");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let W, H, pts = [], raf;

  const N = () => window.innerWidth < 700 ? 28 : 55;

  function resize() {
    W = c.width = window.innerWidth * devicePixelRatio;
    H = c.height = window.innerHeight * devicePixelRatio;
    c.style.cssText = `width:100%;height:100%;position:fixed;inset:0;z-index:0;pointer-events:none`;
  }
  function spawn() {
    pts = [];
    for (let i = 0; i < N(); i++) pts.push({
      x: Math.random() * W,
      y: Math.random() * H + H,
      vx: (Math.random() - .5) * .09 * devicePixelRatio,
      vy: -(Math.random() * .22 + .06) * devicePixelRatio,
      r: (Math.random() * 1.8 + .4) * devicePixelRatio,
      a: Math.random() * .55 + .2,
      drift: Math.random() * Math.PI * 2,
    });
  }
  function draw() {
    ctx.clearRect(0, 0, W, H);
    for (const p of pts) {
      p.y += p.vy;
      p.x += p.vx + Math.sin(p.drift += .008) * .04 * devicePixelRatio;
      if (p.y < -10) { p.y = H + 10; p.x = Math.random() * W; }
      const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 3);
      g.addColorStop(0, `rgba(255,200,100,${p.a})`);
      g.addColorStop(.5, `rgba(232,74,0,${p.a * .6})`);
      g.addColorStop(1, "rgba(232,74,0,0)");
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 3, 0, Math.PI * 2);
      ctx.fillStyle = g; ctx.fill();
    }
    raf = requestAnimationFrame(draw);
  }

  resize(); spawn();
  if (!reduce) draw();
  let rt;
  window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { resize(); spawn(); }, 250); });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) cancelAnimationFrame(raf);
    else if (!reduce) draw();
  });
})();

/* ═══ DEMO CARD TYPEWRITER ════════════════════════════════ */
(function demoTypewriter() {
  const el = $("#demoText");
  if (!el) return;
  const text = `<strong>Polymorphism</strong> means "many forms" — it lets one interface work with different underlying types. In OOP, a parent class reference can hold a child class object, and the correct method is resolved at runtime through <strong>dynamic dispatch</strong>.`;
  let i = 0, visible = "";
  const words = text.split(/(?<=\s)/);

  function type() {
    if (i >= words.length) return;
    visible += words[i++];
    el.innerHTML = visible;
    $("#demoCursor").style.display = i < words.length ? "none" : "inline-block";
    setTimeout(type, 45 + Math.random() * 30);
  }
  setTimeout(type, 1400);
})();

/* ═══ MARKDOWN ═════════════════════════════════════════════ */
function esc(s) { return s.replace(/&/g,"&").replace(/</g,"<").replace(/>/g,">"); }

function md(text) {
  let h = esc(text);
  h = h.replace(/```(\w*)\n?([\s\S]*?)```/g, (_,lang,code) => `<pre><code class="lang-${lang}">${code.trim()}</code></pre>`);
  h = h.replace(/`([^`]+)`/g, "<code>$1</code>");
  h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  h = h.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  h = h.replace(/^#{1,3} (.+)$/gm, "<p><strong>$1</strong></p>");
  h = h.replace(/^[-*] (.+)$/gm, "<li>$1</li>").replace(/(<li>[\s\S]+?<\/li>)+/g, s => `<ul>${s}</ul>`);
  h = h.replace(/^\d+\. (.+)$/gm, "<li>$1</li>").replace(/(?:^|\n)(<li>[\s\S]+?<\/li>)+/g, s => `<ol>${s.trim()}</ol>`);
  return h.split(/\n{2,}/).map(b =>
    /^<(ul|ol|pre|p)/.test(b.trim()) ? b : `<p>${b.replace(/\n/g,"<br>")}</p>`
  ).join("");
}

/* ═══ CHAT: RENDER ═════════════════════════════════════════ */
function hideWelcome() { const w = $("#welcome"); if (w) w.style.display = "none"; }

function addUserMsg(text) {
  hideWelcome();
  const wrap = mk("div", "msg msg-user");
  const bubble = mk("div", "bubble");
  bubble.innerHTML = esc(text).replace(/\n/g,"<br>");
  wrap.append(bubble);
  $("#messages").append(wrap);
  scrollChat();
  return bubble;
}

function addBotSlot(agentLabel) {
  hideWelcome();
  const wrap = mk("div", "msg msg-bot");
  const header = mk("div", "bot-header");
  const label = agentLabel || "Fikaryaar";
  const icon = agentLabel === "Muhaqqiq" ? "🔬" : "";
  header.innerHTML = `<span class="bot-flame" aria-hidden="true">${icon}</span><span class="bot-name">${esc(label)}</span>`;
  const bubble = mk("div", "bubble");
  const typing = mk("div", "typing");
  typing.innerHTML = "<span></span><span></span><span></span>";
  bubble.append(typing);
  wrap.append(header, bubble);
  $("#messages").append(wrap);
  scrollChat();
  return bubble;
}

function attachSources(bubble, sources) {
  if (!sources?.length) return;
  const row = mk("div", "sources-row");
  sources.forEach((s, i) => {
    const chip = mk("span", "src-chip");
    if (s.snippet) chip.dataset.tip = s.snippet;
    chip.innerHTML = `<span class="s-num">${i+1}</span>${esc(s.name)}`;
    row.append(chip);
  });
  bubble.append(row);
}

function scrollChat() { const c = $("#chat"); c.scrollTop = c.scrollHeight; }

/* ═══ CHAT: SUBMIT ═════════════════════════════════════════ */
const ta = $("#question");
ta.addEventListener("input", () => {
  ta.style.height = "auto";
  ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  $("#sendBtn").disabled = !ta.value.trim();
  const len = ta.value.length;
  const hint = $("#charHint");
  hint.textContent = len > 200 ? `${len}` : "";
});
ta.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#composer").requestSubmit(); }
});

$("#composer").addEventListener("submit", async e => {
  e.preventDefault();
  const q = ta.value.trim();
  if (!q || state.streaming) return;

  addUserMsg(q);
  state.history.push({ role: "user", content: q });
  ta.value = ""; ta.style.height = "auto"; $("#sendBtn").disabled = true;
  state.streaming = true;

  if (state.agent === "muhaqqiq") {
    const bubble = addBotSlot("Muhaqqiq");
    try {
      const res = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          history: [],
          agent: "muhaqqiq",
          muhaqqiq_mode: state.muhaqqiqMode,
          source_filter: state.muhaqqiqSource || null,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader(), dec = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const frames = buf.split("\n\n"); buf = frames.pop();
        for (const frame of frames) {
          let evt = "message", data = "";
          for (const ln of frame.split("\n")) {
            if (ln.startsWith("event:")) evt = ln.slice(6).trim();
            else if (ln.startsWith("data:")) data += ln.slice(5).trim();
          }
          if (!data) continue;
          let p; try { p = JSON.parse(data); } catch { continue; }
          if (evt === "status") {
            bubble.innerHTML = `<div class="typing"><span></span><span></span><span></span></div>`;
          } else if (evt === "muhaqqiq") {
            bubble.innerHTML = renderMuhaqqiqCard(p.mode, p.data);
            scrollChat();
          }
        }
      }
    } catch(err) {
      bubble.innerHTML = `<p>Connection error: ${esc(err.message)}</p>`;
    } finally {
      state.streaming = false;
      $("#sendBtn").disabled = !ta.value.trim();
    }
    return;
  }

  // --- Ustad streaming path ---
  const bubble = addBotSlot("Ustad");
  let text = "", srcsShown = false;

  try {
    const res = await fetch(`${API}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, history: state.history.slice(-8, -1), agent: "ustad" }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const reader = res.body.getReader(), dec = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const frames = buf.split("\n\n"); buf = frames.pop();
      for (const frame of frames) {
        let evt = "message", data = "";
        for (const ln of frame.split("\n")) {
          if (ln.startsWith("event:")) evt = ln.slice(6).trim();
          else if (ln.startsWith("data:")) data += ln.slice(5).trim();
        }
        if (!data) continue;
        let p; try { p = JSON.parse(data); } catch { continue; }

        if (evt === "sources") {
          if (!srcsShown) { bubble.innerHTML = ""; srcsShown = true; }
          attachSources(bubble, p.sources);
        } else if (evt === "token") {
          if (!srcsShown) { bubble.innerHTML = ""; srcsShown = true; }
          text += p.token;
          bubble.innerHTML = md(text);
          scrollChat();
        } else if (evt === "done") {
          if (!text) bubble.innerHTML = "<em>No answer found in your notes.</em>";
        }
      }
    }
    state.history.push({ role: "assistant", content: text });
  } catch(err) {
    bubble.innerHTML = `<p>Connection error: ${esc(err.message)}. Is the server running?</p>`;
  } finally {
    state.streaming = false;
    $("#sendBtn").disabled = !ta.value.trim();
  }
});

/* suggestion chips */
function wireChips() {
  $$(".chip").forEach(b => {
    if (b.dataset.wired) return;
    b.dataset.wired = "1";
    b.addEventListener("click", () => {
      if (state.view !== "chat") go("chat");
      setTimeout(() => {
        ta.value = b.dataset.q;
        ta.dispatchEvent(new Event("input"));
        $("#composer").requestSubmit();
      }, state.view !== "chat" ? 60 : 0);
    });
  });
}
wireChips();

/* ═══ UPLOAD ═══════════════════════════════════════════════ */
$("#fileInput").addEventListener("change", async e => {
  const files = [...e.target.files]; e.target.value = "";
  if (files.length) await doUpload(files);
});

// sidebar upload button triggers same input
$("#sidebarUpload")?.addEventListener("click", () => $("#fileInput").click());

// drop zone
const dz = $("#dropZone");
dz?.addEventListener("dragover", e => { e.preventDefault(); dz.classList.add("drag-over"); });
dz?.addEventListener("dragleave", () => dz.classList.remove("drag-over"));
dz?.addEventListener("drop", async e => {
  e.preventDefault(); dz.classList.remove("drag-over");
  const files = [...e.dataTransfer.files].filter(f => /\.(pdf|docx|pptx|md|txt|markdown)$/i.test(f.name));
  if (files.length) await doUpload(files);
});

// global drop
document.addEventListener("dragover", e => e.preventDefault());
document.addEventListener("drop", async e => {
  e.preventDefault();
  const files = [...(e.dataTransfer?.files || [])].filter(f => /\.(pdf|docx|pptx|md|txt|markdown)$/i.test(f.name));
  if (files.length) await doUpload(files);
});

async function doUpload(files) {
  const ut = $("#uploadToast"), utText = $("#utText"), utFill = $("#utFill");
  utText.textContent = `Uploading ${files.length} file${files.length > 1 ? "s" : ""}…`;
  utFill.style.width = "0%";
  ut.classList.add("show");

  const fd = new FormData();
  files.forEach(f => fd.append("files", f));

  try {
    // fake progress
    let prog = 0;
    const tick = setInterval(() => { prog = Math.min(prog + 8, 85); utFill.style.width = prog + "%"; }, 200);

    const res = await fetch(`${API}/upload`, { method: "POST", body: fd });
    const data = await res.json();
    clearInterval(tick);

    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    utFill.style.width = "100%";
    setTimeout(() => ut.classList.remove("show"), 900);
    toast(`✓ Added ${data.chunks_added} chunks from ${data.files.length} file${data.files.length > 1 ? "s" : ""}`, "ok");
    await loadSourcesAndStats();
  } catch(err) {
    ut.classList.remove("show");
    toast(`Upload failed: ${err.message}`, "err");
  }
}

/* ═══ SOURCES & STATS ══════════════════════════════════════ */
async function loadSourcesAndStats() {
  await Promise.all([loadSources(), loadStats()]);
}

async function loadSources() {
  try {
    const res = await fetch(`${API}/sources?t=${Date.now()}`);
    const d = await res.json();
    const sources = d.sources || [];

    // KB panel list
    const list = $("#sourceList");
    list.innerHTML = "";
    if (!sources.length) {
      list.innerHTML = '<li class="empty-note">No notes uploaded yet.</li>';
    } else {
      sources.forEach(s => {
        const li = mk("li", "src-item");
        li.innerHTML = `<span class="src-type">${esc((s.type||"?").toUpperCase())}</span><span class="src-name" title="${esc(s.name)}">${esc(s.name)}</span>`;
        const del = mk("button", "src-del"); del.textContent = "✕"; del.title = "Remove";
        del.addEventListener("click", async () => {
          if (!confirm(`Remove "${s.name}"?`)) return;
          const r = await fetch(`${API}/sources/${encodeURIComponent(s.name)}`, { method: "DELETE" });
          if (r.ok) { toast("Removed", "ok"); loadSourcesAndStats(); }
        });
        li.append(del); list.append(li);
      });
    }

    // chat sidebar
    syncSidebar(sources);

    // quiz file picker
    syncQuizPicker(sources);

    // muhaqqiq source select
    syncMuhaqqiqSources(sources);
  } catch { /* silent */ }
}

function syncSidebar(sources) {
  const list = $("#sidebarSourceList");
  if (!list) return;
  list.innerHTML = "";
  if (!sources?.length) {
    list.innerHTML = '<li class="cs-empty">No notes yet</li>';
    return;
  }
  sources.forEach(s => {
    const li = mk("li", "cs-item");
    li.innerHTML = `<span class="cs-type">${esc((s.type||"?").toUpperCase())}</span><span class="cs-name" title="${esc(s.name)}">${esc(s.name)}</span>`;
    list.append(li);
  });
}

async function loadStats() {
  try {
    const res = await fetch(`${API}/health?t=${Date.now()}`);
    const d = await res.json();

    const chunks = d.chunks || 0, sources = d.sources || 0;
    $("#chunkCount").textContent = chunks.toLocaleString();
    $("#sourceCount").textContent = sources;
    $("#sideChunkCount").textContent = chunks.toLocaleString();
    $("#kbSubtitle").textContent = `${sources} source${sources !== 1 ? "s" : ""} · ${chunks.toLocaleString()} chunks`;

    const dot = $("#statusDot"), txt = $("#statusText");
    if (d.llm_configured && chunks > 0) {
      dot.className = "status-dot ok"; txt.textContent = "Ready";
    } else if (!d.llm_configured) {
      dot.className = "status-dot err"; txt.textContent = "No API key";
    } else {
      dot.className = "status-dot"; txt.textContent = "No notes";
    }
  } catch {
    $("#statusDot").className = "status-dot err";
    $("#statusText").textContent = "Offline";
  }
}

$("#refreshSources").addEventListener("click", loadSourcesAndStats);

/* ═══ ABOUT MODAL ══════════════════════════════════════════ */
const aboutModal = $("#aboutModal");
$("#aboutLink").addEventListener("click", () => aboutModal.classList.add("open"));
$("#modalClose").addEventListener("click", () => aboutModal.classList.remove("open"));
aboutModal.addEventListener("click", e => { if (e.target === aboutModal) aboutModal.classList.remove("open"); });
document.addEventListener("keydown", e => {
  if (e.key === "Escape") { aboutModal.classList.remove("open"); closeKB(); closeMobileMenu(); }
});

/* ═══ INIT ══════════════════════════════════════════════════ */
go("home");
loadSourcesAndStats();
setInterval(loadStats, 30000);

/* ═══ QUIZ ════════════════════════════════════════════════ */
const quizState = { sessionId: null, currentQ: 1, totalQ: 5, pendingEval: null };

$("#startQuiz")?.addEventListener("click", startQuiz);
$("#quizTopic")?.addEventListener("keydown", e => { if (e.key === "Enter") startQuiz(); });
$("#submitAnswer")?.addEventListener("click", submitQuizAnswer);
$("#nextQuestion")?.addEventListener("click", showNextQuestion);
$("#quitQuiz")?.addEventListener("click", () => { go("home"); resetQuiz(); });
$("#retakeQuiz")?.addEventListener("click", () => { resetQuiz(); $("#quizSetup").style.display = ""; $("#quizActive").style.display = "none"; $("#quizReport").style.display = "none"; });

async function startQuiz() {
  const topic = $("#quizTopic")?.value.trim();
  if (!topic) { toast("Enter a topic first", "err"); return; }

  const sourceFilter = $("#quizFileSelect")?.value || null;

  const btn = $("#startQuiz");
  btn.disabled = true; btn.querySelector("span").textContent = "Generating…";

  try {
    const res = await fetch("/api/quiz/start", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, difficulty: "auto", source_filter: sourceFilter })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to start quiz");

    quizState.sessionId = data.session_id;
    quizState.currentQ = 1;
    quizState.totalQ = data.total_questions;

    $("#qaTopic").textContent = data.topic;
    showQuestion(data.first_question);
    $("#quizSetup").style.display = "none";
    $("#quizActive").style.display = "";
  } catch(err) {
    toast(`Quiz error: ${err.message}`, "err");
  } finally {
    btn.disabled = false; btn.querySelector("span").textContent = "Start امتحان";
  }
}

function showQuestion(q) {
  $("#qaProgress").textContent = `Question ${q.num}/${quizState.totalQ}`;
  $("#qaLevel").textContent = q.level_label || q.level;
  $("#qaQuestion").textContent = q.question;
  $("#qaAnswer").value = "";
  $("#qaFeedback").style.display = "none";
  $("#qaFeedback").className = "qa-feedback";
  $("#nextQuestion").style.display = "none";
  const btn = $("#submitAnswer");
  btn.style.display = "";
  btn.disabled = false;
  btn.querySelector("span").textContent = "Submit answer";
  $("#qaAnswer").focus();
  quizState.pendingEval = null;
}

async function submitQuizAnswer() {
  const answer = $("#qaAnswer").value.trim();
  if (!answer) { toast("Write an answer first", "err"); return; }
  
  const btn = $("#submitAnswer");
  btn.disabled = true; btn.querySelector("span").textContent = "Evaluating…";
  
  try {
    const res = await fetch("/api/quiz/answer", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: quizState.sessionId, question_num: quizState.currentQ, answer })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Evaluation failed");
    
    showEvaluation(data.evaluation);
    quizState.pendingEval = data;
    btn.style.display = "none";
    
    const nq = $("#nextQuestion");
    nq.style.display = "";
    if (data.is_last) {
      nq.querySelector("span").textContent = "Finish Quiz & View Results →";
    } else {
      nq.querySelector("span").textContent = "Next question →";
    }
  } catch(err) {
    toast(`Error: ${err.message}`, "err");
    btn.disabled = false; btn.querySelector("span").textContent = "Submit answer";
  }
}

function showEvaluation(ev) {
  const fb = $("#qaFeedback");
  const correct = ev.is_correct === true ? "correct" : ev.is_correct === "partial" ? "partial" : "wrong";
  const emoji = { correct: "✅", partial: "⚡", wrong: "❌" }[correct];
  const label = { correct: "Correct!", partial: "Partially correct", wrong: "Not quite" }[correct];
  const score = ev.score ?? 0;
  
  fb.className = `qa-feedback ${correct}`;
  fb.innerHTML = `
    <div class="qf-verdict">${emoji} ${label} — ${score}/10</div>
    <div class="qf-text">${esc(ev.feedback || "")}</div>
    ${ev.what_was_missed ? `<div class="qf-missed">📌 Missed: ${esc(ev.what_was_missed)}</div>` : ""}
    ${ev.correct_explanation ? `<div class="qf-answer"><strong>Complete answer:</strong><br>${esc(ev.correct_explanation)}</div>` : ""}
  `;
  fb.style.display = "";
}

function showNextQuestion() {
  const data = quizState.pendingEval;
  if (data?.is_last) {
    showReport(data.report);
    return;
  }
  if (!data?.next_question) return;
  quizState.currentQ = data.next_question_num;
  showQuestion(data.next_question);
}

function showReport(report) {
  $("#quizActive").style.display = "none";
  const rep = $("#quizReport");
  rep.style.display = "";
  
  $("#qrGrade").textContent = report.grade || "—";
  $("#qrScore").textContent = `${report.total_score}/${report.max_score} · ${report.percentage}%`;
  $("#qrUrdu").textContent = report.urdu_encouragement || "";
  
  const bars = $("#qrBars");
  bars.innerHTML = "";
  (report.per_question_scores || []).forEach((s, i) => {
    const h = Math.max(8, s * 6);
    bars.innerHTML += `<div class="qr-bar"><div class="qr-bar-score">${s}</div><div class="qr-bar-fill" style="height:${h}px"></div><div class="qr-bar-label">Q${i+1}</div></div>`;
  });
}

function resetQuiz() {
  quizState.sessionId = null; quizState.currentQ = 1;
  $("#quizTopic").value = "";
  $("#quizSetup").style.display = "";
  $("#quizActive").style.display = "none";
  $("#quizReport").style.display = "none";
}

/* ═══ QUIZ FILE PICKER ═════════════════════════════════════ */
function syncQuizPicker(sources) {
  const noFile = $("#qsNoFile");
  const form = $("#qsForm");
  const picker = $("#qsFilePicker");
  const sel = $("#quizFileSelect");

  if (!sources || sources.length === 0) {
    // No files — show no-file state
    if (noFile) noFile.style.display = "";
    if (form) form.style.display = "none";
    return;
  }

  // 1 or more files — show form
  if (noFile) noFile.style.display = "none";
  if (form) form.style.display = "";

  if (sources.length >= 2) {
    // Show the file picker dropdown
    if (picker) picker.style.display = "";
    if (sel) {
      sel.innerHTML = '<option value="">— All uploaded notes —</option>';
      sources.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.name;
        opt.textContent = s.name;
        sel.appendChild(opt);
      });
    }
  } else {
    // Exactly 1 file — hide picker
    if (picker) picker.style.display = "none";
  }
}

/* ═══ MUHAQQIQ SOURCE SELECT ══════════════════════════════ */
function syncMuhaqqiqSources(sources) {
  const sel = $("#mqSourceSelect");
  if (!sel) return;
  sel.innerHTML = '<option value="">— pick a paper —</option>';
  (sources || []).forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.name;
    opt.textContent = s.name;
    sel.appendChild(opt);
  });
}

/* ═══ AGENT SELECTOR ══════════════════════════════════════ */
$$(".agent-pill").forEach(btn => {
  btn.addEventListener("click", () => {
    state.agent = btn.dataset.agent;
    $$(".agent-pill").forEach(b => b.classList.toggle("active", b === btn));
    const mqBar = $("#muhaqqiqBar");
    const ta = $("#question");
    if (state.agent === "muhaqqiq") {
      mqBar.style.display = "";
      ta.placeholder = "Ask a claim to cross-examine, or just press Analyze Paper above…";
    } else {
      mqBar.style.display = "none";
      ta.placeholder = "Ask anything from your notes…";
    }
  });
});

$("#mqSourceSelect")?.addEventListener("change", e => {
  state.muhaqqiqSource = e.target.value;
});

$$(".mq-mode-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    state.muhaqqiqMode = btn.dataset.mode;
    $$(".mq-mode-btn").forEach(b => b.classList.toggle("active", b === btn));
    const ta = $("#question");
    if (state.muhaqqiqMode === "analyze") {
      ta.placeholder = "Press send to analyze the selected paper…";
    } else if (state.muhaqqiqMode === "cross_examine") {
      ta.placeholder = "Enter a claim or hypothesis to cross-examine against the paper…";
    } else if (state.muhaqqiqMode === "synthesize") {
      ta.placeholder = "Press send to synthesize and compare all uploaded papers…";
    }
  });
});

/* ═══ MUHAQQIQ CARD RENDERER ══════════════════════════════ */
function renderMuhaqqiqCard(mode, data) {
  if (data.error) {
    return `<div class="mq-card mq-error"><strong>⚠️ Error:</strong> ${esc(data.error)}</div>`;
  }

  if (mode === "analyze") {
    const m = data.paper_meta || {};
    const delta = data.the_delta || {};
    const intuition = data.core_intuition || {};
    const evidence = data.evidence_anchor || {};
    const blind = data.blindspots_and_critique || {};
    return `
      <div class="mq-card">
        <div class="mq-card-header">
          <span class="mq-badge">🔍 Analysis</span>
          <span class="mq-type">${esc(m.estimated_contribution_type || "")}</span>
        </div>
        <div class="mq-thesis">${esc(m.core_thesis_one_sentence || "")}</div>
        <div class="mq-section">
          <div class="mq-section-title">⚡ The Delta</div>
          <div class="mq-section-body">
            <strong>Previous limitations:</strong>
            <ul>${(delta.previous_limitations || []).map(p => `<li>${esc(p)}</li>`).join("")}</ul>
            <strong>Novel fix:</strong> ${esc(delta.the_novel_fix || "")}
          </div>
        </div>
        <div class="mq-section">
          <div class="mq-section-title">🧠 Core Intuition</div>
          <div class="mq-section-body">
            <p><em>${esc(intuition.simplified_analogy || "")}</em></p>
            <p>${esc(intuition.technical_engine || "")}</p>
          </div>
        </div>
        <div class="mq-section">
          <div class="mq-section-title">📊 Evidence</div>
          <div class="mq-section-body">
            <ul>${(evidence.key_experiments_or_proofs || []).map(p => `<li>${esc(p)}</li>`).join("")}</ul>
            <strong>⭐ Standout result:</strong> ${esc(evidence.strongest_metric_or_finding || "")}
          </div>
        </div>
        <div class="mq-section mq-blindspot">
          <div class="mq-section-title">🕳️ Blindspots</div>
          <div class="mq-section-body">
            <strong>Stated by authors:</strong>
            <ul>${(blind.explicit_limitations || []).map(p => `<li>${esc(p)}</li>`).join("")}</ul>
            <strong>Hidden trade-offs:</strong>
            <ul>${(blind.hidden_compromises || []).map(p => `<li>${esc(p)}</li>`).join("")}</ul>
          </div>
        </div>
      </div>`;
  }

  if (mode === "cross_examine") {
    const verdictColors = { SUPPORTED: "mq-supported", INFERRED: "mq-inferred", CONTRADICTED: "mq-contradicted", UNADDRESSED: "mq-unaddressed" };
    const v = data.verdict || "UNADDRESSED";
    return `
      <div class="mq-card">
        <div class="mq-card-header">
          <span class="mq-badge">⚖️ Cross-Examination</span>
          <span class="mq-verdict ${verdictColors[v] || ""}">${esc(v)}</span>
          <span class="mq-confidence">Confidence: ${((data.confidence_score || 0) * 100).toFixed(0)}%</span>
        </div>
        <div class="mq-section">
          <div class="mq-section-title">Verdict explanation</div>
          <div class="mq-section-body">${esc(data.verdict_explanation || "")}</div>
        </div>
        <div class="mq-section">
          <div class="mq-section-title">📎 Exact quotes from paper</div>
          <div class="mq-section-body">
            ${(data.exact_evidence_quotes || []).map(q => `<blockquote class="mq-quote">${esc(q)}</blockquote>`).join("")}
          </div>
        </div>
        <div class="mq-section">
          <div class="mq-section-title">🔄 Counter-arguments</div>
          <div class="mq-section-body">${esc(data.counter_arguments_found || "None found.")}</div>
        </div>
      </div>`;
  }

  if (mode === "synthesize") {
    const matrix = data.comparative_matrix || [];
    const alignments = data.structural_alignments || [];
    const divs = data.divergences_and_contradictions || [];
    const gaps = data.unresolved_research_gaps || [];
    return `
      <div class="mq-card">
        <div class="mq-card-header"><span class="mq-badge">🧬 Synthesis</span></div>
        <div class="mq-thesis">${esc(data.synthesis_overview || "")}</div>
        <div class="mq-section">
          <div class="mq-section-title">📊 Comparative Matrix</div>
          <div class="mq-section-body">
            <table class="mq-table">
              <thead><tr><th>Paper</th><th>Methodology</th><th>Advantage</th><th>Drawback</th></tr></thead>
              <tbody>${matrix.map(r => `<tr><td>${esc(r.paper_title||"?")}</td><td>${esc(r.core_methodology||"?")}</td><td>${esc(r.primary_advantage||"?")}</td><td>${esc(r.primary_drawback||"?")}</td></tr>`).join("")}</tbody>
            </table>
          </div>
        </div>
        <div class="mq-section">
          <div class="mq-section-title">🤝 Alignments</div>
          <div class="mq-section-body">${alignments.map(a => `<p><strong>${esc(a.shared_concept||"")}:</strong> ${esc(a.supporting_evidence||"")}</p>`).join("")}</div>
        </div>
        <div class="mq-section">
          <div class="mq-section-title">⚡ Contradictions</div>
          <div class="mq-section-body">${divs.map(d => `<p><strong>${esc(d.point_of_contention||"")}:</strong><br>A: ${esc(d.paper_a_stance||"")} | B: ${esc(d.paper_b_stance||"")}</p>`).join("")}</div>
        </div>
        <div class="mq-section mq-blindspot">
          <div class="mq-section-title">🕳️ Unresolved Gaps</div>
          <div class="mq-section-body"><ul>${gaps.map(g => `<li>${esc(g)}</li>`).join("")}</ul></div>
        </div>
      </div>`;
  }

  return `<div class="mq-card">${esc(JSON.stringify(data, null, 2))}</div>`;
}