"""
Node: rewrite a follow-up question into a standalone one.

Why: when the user says "and what about photosynthesis?" after asking about
biology, retrieval works far better on a self-contained question.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.core.prompts import REWRITE_PROMPT
from app.rag.llm import get_rewrite_llm
from app.rag.state import GraphState

log = get_logger(__name__)

_REWRITE_THRESHOLD_WORDS = 6  # short follow-ups likely need rewriting


async def rewrite_question_node(state: GraphState) -> dict:
    question = state["question"]
    history = state.get("history", "")

    # Only rewrite if it really looks like a follow-up.
    if not history or len(question.split()) >= _REWRITE_THRESHOLD_WORDS:
        return {"question": question}

    try:
        prompt = REWRITE_PROMPT.format(history=history, question=question)
        resp = await get_rewrite_llm().ainvoke(prompt)
        rewritten = str(resp.content).strip().strip('"').strip("'")
        if rewritten and len(rewritten) < 500:
            log.info(f"Rewrote question: {question!r} -> {rewritten!r}")
            return {"question": rewritten}
    except Exception as e:  # noqa: BLE001
        log.warning(f"Question rewrite failed, using original: {e}")

    return {"question": question}
