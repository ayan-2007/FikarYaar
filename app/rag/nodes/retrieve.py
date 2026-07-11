"""
Node: retrieve relevant note chunks from Chroma.

Fetches a larger candidate pool, filters by L2 distance threshold, and logs
scores so retrieval failures are visible in logs.
"""
from __future__ import annotations

from langchain_core.documents import Document

from app.core.logging import get_logger
from app.rag.debug import log_retrieval_results
from app.rag.state import GraphState
from app.rag.vectorstore import retrieve_with_threshold

log = get_logger(__name__)


def retrieve_node(state: GraphState) -> dict:
    question = state["question"]
    scored = retrieve_with_threshold(question)
    log_retrieval_results(question, scored)

    docs: list[Document] = [doc for doc, _ in scored]
    retrieval_scores = {i: score for i, (_, score) in enumerate(scored)}

    if not docs:
        from app.core.config import settings

        log.warning(
            f"No chunks passed similarity threshold for: {question[:80]!r} "
            f"(max_distance={settings.retrieval_max_distance})"
        )

    log.info(f"Retrieved {len(docs)} chunk(s) after threshold for: {question[:60]!r}")
    return {
        "documents": docs,
        "sources": [],
        "retrieval_scores": retrieval_scores,
    }
