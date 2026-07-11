"""
Node: generate the final answer from the graded note chunks.
"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from app.core.logging import get_logger
from app.core.prompts import SYSTEM_PROMPT
from app.rag.debug import log_final_prompt
from app.rag.llm import get_llm
from app.rag.state import GraphState

log = get_logger(__name__)

_HUMAN_TEMPLATE = "Question: {question}\n\nAnswer using ONLY the study notes above."


def _format_context(docs) -> str:
    if not docs:
        return "(No relevant notes were found.)"

    # Most relevant chunk last (closest to the human question turn).
    ordered = list(reversed(docs))
    parts = []
    for i, d in enumerate(ordered, 1):
        src = d.metadata.get("source_name", "notes")
        section = d.metadata.get("section")
        page = d.metadata.get("page")
        header = f"[{i}] (from {src}"
        if section:
            header += f", {section}"
        elif page is not None:
            header += f", page {page}"
        header += ")"
        parts.append(f"{header}\n{d.page_content}")
    return "\n\n".join(parts)


def generate_node(state: GraphState) -> dict:
    docs = state.get("documents", [])
    question = state["question"]

    context = _format_context(docs)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", _HUMAN_TEMPLATE),
        ]
    )
    chain = prompt | get_llm()

    messages = prompt.format_messages(context=context, question=question)
    log_final_prompt(messages[0].content, messages[1].content)

    try:
        resp = chain.invoke({"context": context, "question": question})
        answer = str(resp.content).strip()
    except Exception as e:  # noqa: BLE001
        log.error(f"Generation failed: {e}")
        return {
            "answer": (
                "Sorry — I had trouble contacting the language model. "
                "Please check that GROQ_API_KEY is set and try again."
            ),
            "error": str(e),
        }

    log.info(f"Generated answer ({len(answer)} chars)")
    return {"answer": answer}
