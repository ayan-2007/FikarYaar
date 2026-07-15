import json
import re
from typing import Dict

from app.rag.llm import get_llm

SYSTEM = """You are the Doorkeeper of Fikaryaar, an AI study companion.

Classify the user message into exactly ONE category and respond ONLY with valid JSON.

Categories:
- GREETING: hi, hello, salam, thanks, how are you, آداب، کیسے ہو، شکریہ، or any pleasantry
- VALID_STUDY: any academic question (science, math, CS, history, medicine, law, engineering, languages, etc.)
- OFF_TOPIC: non-academic personal questions (food, sports, relationships, news, entertainment)
- QUIZ_REQUEST: user asks for a quiz, test, practice questions, امتحان، or to be tested

Rule: when in doubt between VALID_STUDY and OFF_TOPIC → choose VALID_STUDY.

Respond ONLY with this JSON and nothing else:
{
  "decision": "GREETING|VALID_STUDY|OFF_TOPIC|QUIZ_REQUEST",
  "greeting_response": "warm reply if GREETING, else null",
  "refusal_response": "polite refusal if OFF_TOPIC, else null",
  "confidence": 0.95
}"""

GREETINGS_FAST = {"hi", "hello", "hey", "salam", "السلام علیکم", "آداب", "assalam", "thanks", "thank you", "شکریہ", "thx"}

async def classify(question: str) -> Dict:
    """Fast path for pure greetings, then LLM for ambiguous cases."""
    q_lower = question.strip().lower()
    
    # Fast path — no API call needed for pure greetings
    if q_lower in GREETINGS_FAST or (len(q_lower) <= 12 and any(g in q_lower for g in GREETINGS_FAST)):
        return {
            "decision": "GREETING",
            "greeting_response": _warm_greeting(question),
            "refusal_response": None,
            "confidence": 1.0
        }
    
    llm = get_llm(temperature=0.0)
    
    try:
        resp = await llm.ainvoke(f"User message: {question}")
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.content.strip(), flags=re.MULTILINE).strip()
        result = json.loads(text)
        if "decision" not in result:
            raise ValueError("missing decision")
        return result
    except Exception:
        # Safe default — treat as study question
        return {"decision": "VALID_STUDY", "greeting_response": None, "refusal_response": None, "confidence": 0.5}

def _warm_greeting(q: str) -> str:
    greetings = [
        "وعلیکم السلام! Welcome to Fikaryaar — your study companion. Upload your notes and ask me anything from them. I'm here to help you learn! 📚",
        "Hello! Great to have you here. I'm Fikaryaar — فکریار — your personal AI study buddy. What are we studying today?",
        "آداب! Fikaryaar at your service. I'm ready to answer any questions from your notes — just upload them and fire away!",
        "You're welcome! Remember, I'm always here when you need help with your studies. What topic shall we tackle? 🔥",
    ]
    q_lower = q.lower()
    if "thank" in q_lower or "شکریہ" in q_lower:
        return greetings[3]
    if "سلام" in q_lower or "علیکم" in q_lower:
        return greetings[0]
    return greetings[1]