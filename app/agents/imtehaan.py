import json
import re
import uuid
from typing import List, Dict

from app.rag.llm import get_llm, get_quiz_llm
from langchain_core.prompts import ChatPromptTemplate

SYSTEM_GENERATOR = """تم فکریار کے امتحان ایجنٹ ہو۔ You are Imtehaan, the Examiner of Fikaryaar.

Generate quiz questions STRICTLY from the provided study material.
Never ask about content not in the chunks.

Generate exactly 5 questions at these levels:
Q1: Easy — direct recall ("What is X?")
Q2: Easy-Medium — understanding ("Explain how X works")
Q3: Medium — application ("How would X be used in Y scenario?")
Q4: Hard — analysis ("Compare X and Y. What are the tradeoffs?")
Q5: Extreme — synthesis ("Design/explain a complete solution using X, Y, Z from the material")

Respond ONLY with this JSON (no markdown, no fences):
{{
  "questions": [
    {{
      "num": 1,
      "level": "easy",
      "question": "...",
      "expected_concepts": ["concept1", "concept2"],
      "model_answer": "the complete correct answer (internal only, never shown to student)"
    }}
  ]
}}"""

SYSTEM_EVALUATOR = """تم فکریار کے امتحان ایجنٹ ہو۔ You evaluate student answers.

Be strict about correctness but generous about phrasing.
A conceptually correct answer in different words = correct.
Partially correct = partial (tell them what they missed).
Wrong = explain why and guide them toward the right answer.
Never just say "wrong" — always teach.

IMPORTANT: Write your evaluation feedback strictly in English, unless the student answered in Urdu.

Respond ONLY with this JSON:
{{
  "is_correct": true/false/"partial",
  "score": 0-10,
  "feedback": "detailed encouraging feedback",
  "what_was_missed": "specific missing concepts (if partial/wrong)",
  "correct_explanation": "the full correct answer clearly explained"
}}"""

# In-memory quiz sessions {session_id: {...}}
_sessions: Dict[str, Dict] = {}

async def start_quiz(topic: str, chunks: List[Dict]) -> Dict:
    """Generate quiz questions from chunks. Returns session_id and first question."""
    
    chunks_text = "\n\n---\n\n".join(
        f"[{c['source']}]\n{c['text'][:800]}" for c in chunks[:8]
    )
    
    llm = get_quiz_llm()
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_GENERATOR),
        ("human", "Topic: {topic}\n\nStudy material:\n{chunks_text}")
    ])
    
    chain = prompt_template | llm
    
    try:
        resp = await chain.ainvoke({"topic": topic, "chunks_text": chunks_text})
        content = resp.content
        if isinstance(content, list):
            content = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', content.strip(), flags=re.MULTILINE).strip()
        data = json.loads(text)
        questions = data["questions"]
    except Exception as e:
        return {"error": f"Failed to generate quiz questions: {str(e)}"}
    
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "topic": topic,
        "questions": questions,
        "current": 0,
        "scores": [],
        "chunks": chunks_text
    }
    
    return {
        "session_id": session_id,
        "total_questions": len(questions),
        "topic": topic,
        "first_question": _format_question(questions[0])
    }

async def evaluate_answer(session_id: str, question_num: int, answer: str) -> Dict:
    """Evaluate answer and return feedback + next question (or final report)."""
    
    if session_id not in _sessions:
        return {"error": "Session not found. Please start a new quiz."}
    
    session = _sessions[session_id]
    questions = session["questions"]
    q_idx = question_num - 1
    
    if q_idx >= len(questions):
        return {"error": "Invalid question number."}
    
    question = questions[q_idx]
    
    # Evaluate
    llm = get_llm(temperature=0.2, max_tokens=800)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_EVALUATOR),
        ("human", "Question: {question}\nLevel: {level}\nExpected concepts: {expected_concepts}\nModel answer: {model_answer}\nStudent's answer: {student_answer}\n\nEvaluate this answer.")
    ])
    
    chain = prompt_template | llm
    
    try:
        resp = await chain.ainvoke({
            "question": question['question'],
            "level": question['level'],
            "expected_concepts": ', '.join(question.get('expected_concepts', [])),
            "model_answer": question.get('model_answer', 'See expected concepts'),
            "student_answer": answer
        })
        content = resp.content
        if isinstance(content, list):
            content = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', content.strip(), flags=re.MULTILINE).strip()
        evaluation = json.loads(text)
    except Exception:
        evaluation = {
            "is_correct": "partial", "score": 5,
            "feedback": "Your answer shows understanding. Keep studying!",
            "what_was_missed": "", "correct_explanation": question.get("model_answer", "")
        }
    
    session["scores"].append(evaluation.get("score", 5))
    session["current"] = question_num
    
    # Check if quiz is complete
    next_q_num = question_num + 1
    is_last = next_q_num > len(questions)
    
    result = {
        "evaluation": evaluation,
        "question_num": question_num,
        "is_last": is_last
    }
    
    if not is_last:
        result["next_question"] = _format_question(questions[next_q_num - 1])
        result["next_question_num"] = next_q_num
    else:
        result["report"] = _generate_report(session)
        del _sessions[session_id]  # cleanup
    
    return result

def _format_question(q: Dict) -> Dict:
    level_labels = {
        "easy": "[Easy]",
        "easy-medium": "[Easy-Medium]",
        "medium": "[Medium]",
        "hard": "[Hard]",
        "extreme": "[Extreme]"
    }
    level = q.get("level", "medium")
    if isinstance(level, str):
        level = level.lower()
    return {
        "num": q.get("num", 1),
        "level": level,
        "question": q.get("question", "[Missing Question]"),
        "level_label": level_labels.get(level, "[Question]")
    }

def _generate_report(session: Dict) -> Dict:
    scores = session["scores"]
    total = sum(scores)
    max_total = len(scores) * 10
    pct = round((total / max_total) * 100) if max_total > 0 else 0
    
    if pct >= 90:
        grade, urdu = "A+", "شاباش! آپ نے بہترین کارکردگی دکھائی — آپ ایک حقیقی طالب علم ہیں!"
    elif pct >= 80:
        grade, urdu = "A", "بہت اچھے! تھوڑی سی محنت اور آپ کامل ہو جائیں گے!"
    elif pct >= 70:
        grade, urdu = "B", "اچھی کوشش! مزید پڑھیں اور آپ ضرور کامیاب ہوں گے!"
    elif pct >= 60:
        grade, urdu = "C", "ٹھیک ہے، لیکن ابھی اور محنت کی ضرورت ہے — ہمت نہ ہاریں!"
    else:
        grade, urdu = "D", "مایوس نہ ہوں — ہر ماہر پہلے ایک مبتدی تھا۔ دوبارہ کوشش کریں!"
    
    return {
        "total_score": total,
        "max_score": max_total,
        "percentage": pct,
        "grade": grade,
        "urdu_encouragement": urdu,
        "per_question_scores": scores
    }