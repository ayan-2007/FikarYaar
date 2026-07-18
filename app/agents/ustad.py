from typing import List, Dict, AsyncGenerator

from app.rag.llm import get_llm

SYSTEM_GROUNDED = """You are Ustad, the Master Teacher of Fikaryaar.

RULES — never break these:
1. Answer STRICTLY from the provided chunks — no external knowledge
2. Use markdown: **bold** key terms, bullet points for lists, code blocks for code
3. Add inline citations [¹] [²] mapped to the source chunks
4. For abstract concepts, include an analogy ("Think of it like...")
5. End every answer with a "💡 **Key Takeaway**:" section — one powerful sentence
6. Be direct — never say "based on the text" or "according to the document"
7. Be encouraging — you believe in this student completely
8. NEVER refuse to answer or say "I don't know" — synthesize what you have

Citation format at the end of your response:
---
**📚 Sources:**
[¹] filename.pdf — "brief quote from chunk..."
[²] notes.docx — "brief quote from chunk..." """

SYSTEM_FALLBACK = """You are Ustad, the Master Teacher of Fikaryaar.

CRITICAL: This topic was NOT found in the student's uploaded notes.

START your response with EXACTLY this block (copy verbatim):
> ⚠️ **This topic wasn't found in your uploaded notes.**
> Answering from general knowledge. Please verify with your course material or upload relevant notes.

Then provide the most thorough, clear, well-structured explanation possible.
Use markdown. Include examples. Use analogies. Be even more detailed than usual.
End with 💡 **Key Takeaway**:

Do NOT include source citations."""

async def stream_answer(
    question: str,
    chunks: List[Dict],
    validation: Dict,
    history: List[Dict]
) -> AsyncGenerator[str, None]:
    """Yields SSE-formatted strings."""
    
    fallback = validation.get("fallback_needed", False)
    
    if fallback:
        system = SYSTEM_FALLBACK
        context = ""
    else:
        system = SYSTEM_GROUNDED
        context = "**Retrieved from your notes:**\n\n" + "\n\n---\n\n".join(
            f"[Chunk {i+1} | {c['source']}]\n{c['text']}"
            for i, c in enumerate(chunks[:6])
        )
    
    # Build conversation history
    history_text = ""
    if history:
        history_text = "\n\n**Previous conversation:**\n" + "\n".join(
            f"{'Student' if h['role'] == 'user' else 'Ustad'}: {h['content'][:300]}"
            for h in history[-4:]
        )
    
    prompt = f"{context}{history_text}\n\n**Student's question:** {question}"
    
    messages = [
        ("system", system),
        ("human", prompt)
    ]
    
    llm = get_llm(temperature=0.4, streaming=True)
    
    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                content = chunk.content
                if isinstance(content, list):
                    # Gemini sometimes returns a list of blocks instead of a string
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and "text" in block:
                            text_parts.append(block["text"])
                        elif isinstance(block, str):
                            text_parts.append(block)
                        else:
                            text_parts.append(str(block))
                    content = "".join(text_parts)
                
                if content:
                    yield str(content)
    except Exception as e:
        yield f"\n\nI encountered an error generating the response: {str(e)}"