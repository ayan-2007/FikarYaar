"""
The LangGraph RAG pipeline.

Flow:
  rewrite  ->  classify  ->  {OFFTOPIC: refuse_offtopic}
                              {STUDY:   retrieve -> grade -> {used_notes: generate}
                                                                 {!used:    refuse_no_notes}}

This single graph encodes all the guardrails. Each node is a plain function in
app/rag/nodes/, so beginners can read the whole flow top-to-bottom.
"""
from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph

from app.core.logging import get_logger
from app.rag.nodes.classify import classify_intent_node
from app.rag.nodes.generate import generate_node
from app.rag.nodes.grade import grade_documents_node
from app.rag.nodes.refuse import refuse_no_notes_node, refuse_offtopic_node
from app.rag.nodes.rewrite import rewrite_question_node
from app.rag.nodes.retrieve import retrieve_node
from app.rag.state import GraphState

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Conditional routers
# ---------------------------------------------------------------------------


def _route_after_classify(state: GraphState) -> Literal["retrieve", "refuse_offtopic"]:
    return "refuse_offtopic" if state.get("intent") == "OFFTOPIC" else "retrieve"


def _route_after_grade(state: GraphState) -> Literal["generate", "refuse_no_notes"]:
    return "generate" if state.get("used_notes") else "refuse_no_notes"


# ---------------------------------------------------------------------------
# Build the compiled graph once and reuse
# ---------------------------------------------------------------------------

def build_graph():
    g = StateGraph(GraphState)

    g.add_node("rewrite", rewrite_question_node)
    g.add_node("classify", classify_intent_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("grade", grade_documents_node)
    g.add_node("generate", generate_node)
    g.add_node("refuse_offtopic", refuse_offtopic_node)
    g.add_node("refuse_no_notes", refuse_no_notes_node)

    g.set_entry_point("rewrite")
    g.add_edge("rewrite", "classify")
    g.add_conditional_edges(
        "classify",
        _route_after_classify,
        {"retrieve": "retrieve", "refuse_offtopic": "refuse_offtopic"},
    )
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges(
        "grade",
        _route_after_grade,
        {"generate": "generate", "refuse_no_notes": "refuse_no_notes"},
    )
    g.add_edge("generate", END)
    g.add_edge("refuse_offtopic", END)
    g.add_edge("refuse_no_notes", END)

    compiled = g.compile()
    log.info("RAG graph compiled")
    return compiled


# Cache the compiled graph for the lifetime of the process.
_compiled = None


def get_graph():
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return _compiled


def format_history(messages: list[dict]) -> str:
    """Turn a chat history list into a short string for the rewrite node."""
    if not messages:
        return ""
    lines = []
    for m in messages[-6:]:  # keep last 3 exchanges
        role = m.get("role", "user")
        content = str(m.get("content", ""))[:300]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def ask(question: str, history: list[dict] | None = None) -> dict:
    """
    Convenience entry point: run the full graph for a single question.

    Returns the final state dict (with keys: answer, sources, used_notes, ...).
    """
    history = history or []
    state: GraphState = {
        "question": question,
        "original_question": question,
        "history": format_history(history),
    }
    result = get_graph().invoke(state)
    return result
