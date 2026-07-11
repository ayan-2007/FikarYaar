"""
Shared state for the RAG graph.

LangGraph passes a state dict between nodes. We define its shape here with a
TypedDict so each node is self-documenting for beginners.
"""
from __future__ import annotations

from typing import List, TypedDict

from langchain_core.documents import Document


class GraphState(TypedDict, total=False):
    """Mutable state threaded through the graph."""

    question: str                 # the (possibly rewritten) user question
    original_question: str        # what the user actually typed
    history: str                  # short conversation history string
    intent: str                   # "STUDY" | "OFFTOPIC"
    documents: List[Document]     # retrieved + graded note chunks
    sources: List[dict]           # metadata about chunks, for the UI
    retrieval_scores: dict        # chunk index -> L2 distance from retrieve step
    answer: str                   # the final assistant message
    used_notes: bool              # did we find anything relevant?
    error: str                    # populated if something went wrong
