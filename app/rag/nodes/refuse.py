"""
Node: the polite refusal used when intent is OFFTOPIC or GREETING.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.rag.state import GraphState

log = get_logger(__name__)

OFFTOPIC_MSG = "I can only help with topics from your study notes."


def refuse_offtopic_node(state: GraphState) -> dict:
    log.info(f"Refusing off-topic question: {state['question'][:60]!r}")
    ans = state.get("answer") or OFFTOPIC_MSG
    return {"answer": ans, "used_notes": False}


def refuse_no_notes_node(state: GraphState) -> dict:
    log.info("No relevant notes found — returning 'no notes' message")
    ans = state.get("answer") or "I don't have that in your notes. Please upload or ask about content covered in your study material."
    return {"answer": ans, "used_notes": False}
