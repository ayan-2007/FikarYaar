"""
Node: grade retrieved documents for relevance.

Vector search + distance threshold still returns loosely related chunks.
This node uses a batched LLM grader to drop irrelevant context before generation.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger
from app.core.prompts import DOC_GRADER_PROMPT
from app.rag.debug import log_graded_chunks
from app.rag.llm import get_grader_llm
from app.rag.state import GraphState

log = get_logger(__name__)

# Single-line verdicts only — give the grader headroom for all chunks.
# At ~2 tokens per YES/NO + newline, 128 safely covers 20+ chunks.
_GRADER_MAX_TOKENS_CAP = 128


def _score_fallback_keep(docs, scores: dict, max_keep: int = 2) -> list[bool]:
    """If the LLM grader fails, keep only the lowest-distance (best) chunks."""
    if not docs:
        return []
    ranked = sorted(range(len(docs)), key=lambda i: scores.get(i, 999.0))
    keep_set = set(ranked[:max_keep])
    return [i in keep_set for i in range(len(docs))]


def _grade_batch(question: str, docs) -> list[bool]:
    """
    Grade every chunk in ONE LLM call.

    Returns a list of booleans (one per chunk), True = keep.
    """
    if not docs:
        return []

    numbered = "\n\n".join(
        f"[Snippet {i + 1}]\n{d.page_content[:1500]}" for i, d in enumerate(docs)
    )
    prompt = DOC_GRADER_PROMPT.format(question=question[:800], documents=numbered)

    try:
        llm = get_grader_llm()
        # Allow enough tokens for every chunk to get its own verdict line.
        # ~4 tokens per doc accounts for YES/NO + newline + small edge-cases.
        llm = llm.bind(max_tokens=max(_GRADER_MAX_TOKENS_CAP, len(docs) * 4 + 16))
        resp = llm.invoke(prompt)
        text = str(resp.content).strip().upper()
    except Exception as e:  # noqa: BLE001
        log.warning(f"Batch grader failed: {e}")
        raise

    verdicts: list[bool] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        token = line.split()[-1] if line.split() else line
        verdicts.append(token.startswith("Y"))

    if len(verdicts) < len(docs):
        verdicts += [False] * (len(docs) - len(verdicts))
    elif len(verdicts) > len(docs):
        verdicts = verdicts[: len(docs)]

    return verdicts


def grade_documents_node(state: GraphState) -> dict:
    question = state["question"]
    docs = state.get("documents", [])
    scores = state.get("retrieval_scores", {})

    if not docs:
        return {"documents": [], "used_notes": False, "sources": []}

    try:
        verdicts = _grade_batch(question, docs)
    except Exception:
        verdicts = _score_fallback_keep(docs, scores)
        log.warning("Using score-based fallback after grader failure")

    kept = [d for d, keep in zip(docs, verdicts) if keep]
    log_graded_chunks(question, kept, dropped=len(docs) - len(kept))

    sources_seen = set()
    sources = []
    for i, d in enumerate(kept):
        name = d.metadata.get("source_name", "unknown")
        section = d.metadata.get("section", "")
        page = d.metadata.get("page")
        label_bits = [name]
        if section:
            label_bits.append(section)
        elif page is not None:
            label_bits.append(f"p.{page}")
        label = " — ".join(label_bits)

        if name in sources_seen:
            continue
        sources_seen.add(name)
        sources.append(
            {
                "name": name,
                "type": d.metadata.get("file_type", "?"),
                "snippet": d.page_content[:180].replace("\n", " ").strip(),
                "section": section,
                "score": scores.get(i),
            }
        )

    return {"documents": kept, "used_notes": len(kept) > 0, "sources": sources}
