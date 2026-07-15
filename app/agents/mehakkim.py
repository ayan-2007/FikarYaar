import json
import re
from typing import List, Dict

from app.rag.llm import get_llm

SYSTEM = """You are the Validator (Mehakkim) of Fikaryaar.

You receive a student's question and retrieved text chunks from their notes.
Evaluate the retrieval quality honestly.

Respond ONLY with valid JSON:
{
  "retrieval_valid": true/false,
  "is_sufficient": true/false,
  "coverage_score": 0-10,
  "can_answer": true/false,
  "fallback_needed": true/false,
  "validator_note": "one sentence for the teacher"
}

Rules:
- retrieval_valid=false if chunks are empty, off-topic, or clearly wrong
- fallback_needed=true if coverage_score < 5 OR retrieval_valid=false
- can_answer=true even if fallback_needed=true (teacher will answer from general knowledge)
- Be strict about relevance, generous about partial coverage"""

async def validate(question: str, chunks: List[Dict]) -> dict:
    # Hard check: no chunks or all scores below threshold
    if not chunks:
        return {
            "retrieval_valid": False, "is_sufficient": False,
            "coverage_score": 0, "can_answer": True,
            "fallback_needed": True,
            "validator_note": "No chunks retrieved — notes may not cover this topic."
        }
    
    top_score = max(c.get("score", 0) for c in chunks)
    if top_score < 0.35:
        return {
            "retrieval_valid": False, "is_sufficient": False,
            "coverage_score": 1, "can_answer": True,
            "fallback_needed": True,
            "validator_note": f"Best similarity score {top_score:.2f} below threshold — topic not in notes."
        }
    
    # Build context for LLM validation
    chunks_text = "\n\n---\n\n".join(
        f"[Chunk {i+1} | score={c['score']:.2f} | {c['source']}]\n{c['text'][:600]}"
        for i, c in enumerate(chunks[:4])
    )
    
    prompt = f"""Question: {question}

Retrieved chunks:
{chunks_text}

Validate whether these chunks sufficiently answer the question."""
    
    llm = get_llm(temperature=0.1)
    
    try:
        messages = [
            ("system", SYSTEM),
            ("human", prompt)
        ]
        resp = await llm.ainvoke(messages)
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.content.strip(), flags=re.MULTILINE).strip()
        return json.loads(text)
    except Exception:
        # If validation fails, proceed with answer — don't block the student
        return {
            "retrieval_valid": True, "is_sufficient": True,
            "coverage_score": 6, "can_answer": True,
            "fallback_needed": False,
            "validator_note": "Validation inconclusive — proceeding with retrieved chunks."
        }