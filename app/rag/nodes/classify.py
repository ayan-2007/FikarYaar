"""
Node: classify intent (STUDY vs OFFTOPIC).

This is the FIRST guardrail. Before we spend tokens on retrieval + generation,
we ask a tiny model call whether the user is even asking a study question.
Anything that looks like creative writing, coding, advice, role-play, or a
prompt-injection attempt gets routed straight to the polite refusal.

We also run a cheap rule-based pre-check so obvious junk is caught without any
API call at all.
"""
from __future__ import annotations

import re

from app.core.logging import get_logger
from app.core.prompts import INTENT_PROMPT
from app.rag.llm import get_grader_llm
from app.rag.state import GraphState

log = get_logger(__name__)

# Patterns that are unambiguously not study questions. Caught locally, no API.
_HARD_OFFTOPIC = [
    r"\bwrite\s+(me\s+)?(a\s+)?(poem|story|song|script|email|essay|tweet|caption)\b",
    r"\btranslate\b",
    r"\bstock\s+price\b",
    r"\bweather\b",
    r"ignore (all |any |previous )?(previous |prior )?instructions",
    r"you are now (a|an) ",
    r"\bact as\b",
    r"\bjailbreak\b",
    r"\bDAN\b",
]
_HARD_OFFTOPIC_RE = [re.compile(p, re.IGNORECASE) for p in _HARD_OFFTOPIC]


def _rule_based_offtopic(question: str) -> bool:
    return any(p.search(question) for p in _HARD_OFFTOPIC_RE)


def classify_intent_node(state: GraphState) -> dict:
    question = state["question"].strip()

    # 1) Fast local check
    if _rule_based_offtopic(question):
        log.info(f"Intent=OFFTOPIC (rule match): {question[:60]!r}")
        return {"intent": "OFFTOPIC"}

    # 2) Model-based classification
    try:
        prompt = INTENT_PROMPT.format(question=question[:1500])
        resp = get_grader_llm().invoke(prompt)
        verdict = str(resp.content).strip().upper().split()[0] if str(resp.content).strip() else ""
        if verdict.startswith("OFF"):
            log.info(f"Intent=OFFTOPIC (model): {question[:60]!r}")
            return {"intent": "OFFTOPIC"}
        if verdict.startswith("STUDY"):
            log.info(f"Intent=STUDY: {question[:60]!r}")
            return {"intent": "STUDY"}
        # Ambiguous answer -> default to STUDY and let later nodes decide.
        log.info("Intent ambiguous -> defaulting to STUDY")
        return {"intent": "STUDY"}
    except Exception as e:  # noqa: BLE001
        # If the grader fails, we don't want to block studying, so we let it
        # through to retrieval, where the doc-grader will catch irrelevant hits.
        log.warning(f"Intent classifier failed ({e}); defaulting to STUDY")
        return {"intent": "STUDY"}
