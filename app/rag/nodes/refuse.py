"""
Node: the polite refusal used when intent is OFFTOPIC or when no notes matched.

Keeping the refusal message constant and non-apologetic-in-detail prevents the
bot from being led into elaborating (which can leak that it's an AI etc.).
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.rag.state import GraphState

log = get_logger(__name__)

NO_NOTES_MSG = (
    "I don't have that in your notes. Please upload or ask about content "
    "covered in your study material."
)
OFFTOPIC_MSG = "I can only help with topics from your study notes."


def refuse_offtopic_node(state: GraphState) -> dict:
    log.info(f"Refusing off-topic question: {state['question'][:60]!r}")
    return {"answer": OFFTOPIC_MSG, "used_notes": False}


def refuse_no_notes_node(state: GraphState) -> dict:
    log.info("No relevant notes found — returning 'no notes' message")
    return {"answer": NO_NOTES_MSG, "used_notes": False}
