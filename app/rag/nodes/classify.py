"""
Node: classify intent using Agent 1 (Darban).
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.agents.darban import classify as darban_classify
from app.rag.state import GraphState

log = get_logger(__name__)


async def classify_intent_node(state: GraphState) -> dict:
    question = state["question"].strip()

    try:
        res = await darban_classify(question)
        decision = res.get("decision", "VALID_STUDY")
        
        if decision == "GREETING":
            log.info(f"Intent=GREETING: {question[:60]!r}")
            return {"intent": "GREETING", "answer": res.get("greeting_response")}
        elif decision == "OFF_TOPIC":
            log.info(f"Intent=OFFTOPIC: {question[:60]!r}")
            refusal = res.get("refusal_response") or "I am just your study buddy, I can't answer this."
            return {"intent": "OFFTOPIC", "answer": refusal}
        elif decision == "QUIZ_REQUEST":
            log.info(f"Intent=QUIZ_REQUEST: {question[:60]!r}")
            return {
                "intent": "QUIZ_REQUEST",
                "answer": (
                    "Sure! Let's start a quiz. Please click on the **Quiz** tab "
                    "at the top of the page, enter your topic, and let's begin! 📝"
                )
            }
        
        log.info(f"Intent=STUDY: {question[:60]!r}")
        return {"intent": "STUDY"}
    except Exception as e:
        log.warning(f"Darban intent classifier failed ({e}); defaulting to STUDY")
        return {"intent": "STUDY"}
