"""
Node: grade retrieved documents using Agent 2 (Mehakkim).
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.agents.mehakkim import validate as mehakkim_validate
from app.rag.state import GraphState

log = get_logger(__name__)


async def grade_documents_node(state: GraphState) -> dict:
    question = state["question"]
    docs = state.get("documents", [])
    scores = state.get("retrieval_scores", {})

    if not docs:
        log.info("No documents retrieved — triggering fallback")
        return {
            "documents": [],
            "used_notes": False,
            "sources": [],
            "validation_result": {"fallback_needed": True}
        }

    # Convert retrieved documents to the dictionary structure expected by Mehakkim
    chunks = []
    for i, d in enumerate(docs):
        chunks.append({
            "source": d.metadata.get("source_name", "unknown"),
            "text": d.page_content,
            "score": scores.get(i, 0.0)
        })

    try:
        res = await mehakkim_validate(question, chunks)
    except Exception as e:
        log.warning(f"Mehakkim validation failed ({e}); falling back to standard retrieval flow")
        res = {
            "retrieval_valid": True,
            "is_sufficient": True,
            "fallback_needed": False,
            "validator_note": "Validation failed, defaulting to grounded generation."
        }

    fallback_needed = res.get("fallback_needed", False) or not res.get("retrieval_valid", False)

    # Format sources for UI if retrieval is valid
    sources = []
    if not fallback_needed:
        sources_seen = set()
        for i, d in enumerate(docs):
            name = d.metadata.get("source_name", "unknown")
            section = d.metadata.get("section", "")
            page = d.metadata.get("page")
            
            if name in sources_seen:
                continue
            sources_seen.add(name)
            sources.append({
                "name": name,
                "type": d.metadata.get("file_type", "?"),
                "snippet": d.page_content[:180].replace("\n", " ").strip(),
                "section": section,
                "score": scores.get(i),
            })

    log.info(f"Mehakkim verdict: fallback_needed={fallback_needed}, note={res.get('validator_note')}")
    return {
        "documents": [] if fallback_needed else docs,
        "used_notes": not fallback_needed,
        "sources": sources,
        "validation_result": res
    }
