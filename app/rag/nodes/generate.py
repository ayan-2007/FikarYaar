"""
Node: generate the final answer using Agent 3 (Ustad).
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.agents.ustad import stream_answer as ustad_stream
from app.rag.state import GraphState

log = get_logger(__name__)


async def generate_node(state: GraphState) -> dict:
    docs = state.get("documents", [])
    question = state["question"]
    validation = state.get("validation_result") or {"fallback_needed": not state.get("used_notes", False)}
    chat_history = state.get("chat_history") or []

    # Map docs to the dict format expected by Ustad
    chunks = [{"source": d.metadata.get("source_name", "unknown"), "text": d.page_content} for d in docs]

    try:
        tokens = []
        # Consume the async generator from Ustad
        async for token in ustad_stream(question, chunks, validation, chat_history):
            tokens.append(token)
        answer = "".join(tokens).strip()
    except Exception as e:
        log.error(f"Ustad generation failed: {e}")
        answer = f"I encountered an error generating the response: {str(e)}"

    log.info(f"Generated answer via Ustad ({len(answer)} chars)")
    return {"answer": answer}
