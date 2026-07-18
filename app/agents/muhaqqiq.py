import json
import re
from typing import List, Dict
from app.rag.llm import get_llm

SYSTEM_ANALYZER = """تم فکریار کے محقق ایجنٹ ہو۔ You are Muhaqqiq, the Research Analyst of Fikaryaar.

Your job is to deconstruct an uploaded research paper deeply, objectively, and critically. 
Do not merely summarize the abstract. Extract the deep structural and architectural truth of the paper based ONLY on the provided text chunks.

Analyze the paper across these exact vectors:
1. THE DELTA: The exact baseline flaw of previous works and what this paper introduces.
2. CORE INTUITION: The fundamental mechanism or thesis simplified.
3. THE PROOF: Key experiments, datasets, or arguments backing the claims.
4. BLINDSPOTS: Critical limitations, hidden costs, assumptions, or gaps left unaddressed.

Respond ONLY with this JSON structure (no markdown fences, no extra text):
{
  "paper_meta": {
    "estimated_contribution_type": "Empirical / Theoretical / Systemic / Review",
    "core_thesis_one_sentence": "..."
  },
  "the_delta": {
    "previous_limitations": ["point 1", "point 2"],
    "the_novel_fix": "What this paper uniquely introduces"
  },
  "core_intuition": {
    "simplified_analogy": "An elegant analogy to understand the mechanism",
    "technical_engine": "The primary formula, architecture, or workflow that makes it work"
  },
  "evidence_anchor": {
    "key_experiments_or_proofs": ["experiment/proof 1", "experiment/proof 2"],
    "strongest_metric_or_finding": "The standout result that validates the paper"
  },
  "blindspots_and_critique": {
    "explicit_limitations": ["stated by authors 1", "stated by authors 2"],
    "hidden_compromises": ["unstated trade-offs like compute, memory, scalability, or bias"]
  }
}"""

SYSTEM_CROSS_EXAMINER = """تم فکریار کے محقق ایجنٹ ہو۔ You are Muhaqqiq. You cross-examine academic claims.

Analyze the student's question/claim against the retrieved research paper text chunks.
Determine if the claim is explicitly supported, inferred, or completely unaddressed/contradicted by the text.

Respond ONLY with this JSON structure:
{
  "verdict": "SUPPORTED | INFERRED | CONTRADICTED | UNADDRESSED",
  "confidence_score": 0.0-1.0,
  "verdict_explanation": "Detailed explanation of why this verdict was reached based on the text.",
  "exact_evidence_quotes": ["quote 1 from chunks", "quote 2 from chunks"],
  "counter_arguments_found": "Any nuances or contradictory data points found in the text regarding this claim."
}"""

SYSTEM_SYNTHESIZER = """تم فکریار کے محقق ایجنٹ ہو۔ You are Muhaqqiq, performing a multi-document literature synthesis.

Your task is to analyze the text chunks extracted from multiple research papers. Compare their methodologies, find common thematic alignments, discover explicit or hidden ideological/technical contradictions, and synthesize unresolved research gaps.

Respond ONLY with this JSON structure (no markdown fences, no extra text):
{
  "synthesis_overview": "A cohesive 2-3 sentence macro-view of how these papers interact conceptually.",
  "comparative_matrix": [
    {
      "paper_title": "Title or filename of Paper",
      "core_methodology": "Main approach used",
      "primary_advantage": "Main benefit over others",
      "primary_drawback": "Main limitation or bottleneck compared to others"
    }
  ],
  "structural_alignments": [
    {
      "shared_concept": "The concept or agreement point",
      "supporting_evidence": "Brief summary of how the papers align on this"
    }
  ],
  "divergences_and_contradictions": [
    {
      "point_of_contention": "Where do these papers disagree?",
      "paper_a_stance": "Stance of Paper A",
      "paper_b_stance": "Stance of Paper B"
    }
  ],
  "unresolved_research_gaps": [
    "An open problem or limitation that NONE of these papers completely solved."
  ]
}"""


async def analyze_paper(chunks: List[Dict]) -> Dict:
    """
    Parses retrieved core chunks of a research paper to generate a deep 
    architectural, structural, and critical critique breakdown.
    """
    if not chunks:
        return {"error": "No research paper text chunks provided for analysis."}

    chunks_text = "\n\n---\n\n".join(
        f"[Source Chunk {i+1} | Page {c.get('metadata', {}).get('page', 'Unknown')} | {c['source']}]\n{c['text'][:1200]}"
        for i, c in enumerate(chunks[:8])
    )

    llm = get_llm(temperature=0.1, max_tokens=1500)
    prompt = f"Deconstruct and evaluate the following research paper text chunks:\n\n{chunks_text}"

    try:
        resp = await llm.ainvoke([
            ("system", SYSTEM_ANALYZER),
            ("human", prompt)
        ])
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.content.strip(), flags=re.MULTILINE).strip()
        return json.loads(text)
    except Exception as e:
        return {
            "paper_meta": {"estimated_contribution_type": "Unknown", "core_thesis_one_sentence": "Analysis compilation encountered an unexpected parsing event."},
            "the_delta": {"previous_limitations": ["Failed to extract structural text"], "the_novel_fix": str(e)},
            "core_intuition": {"simplified_analogy": "N/A", "technical_engine": "N/A"},
            "evidence_anchor": {"key_experiments_or_proofs": [], "strongest_metric_or_finding": "N/A"},
            "blindspots_and_critique": {"explicit_limitations": [], "hidden_compromises": []}
        }


async def cross_examine_claim(claim: str, chunks: List[Dict]) -> Dict:
    """
    Allows a student to pitch a specific hypothesis or question against the paper's content, 
    verifying if the data in the paper genuinely substantiates it.
    """
    if not chunks:
        return {
            "verdict": "UNADDRESSED", 
            "confidence_score": 0.0, 
            "verdict_explanation": "No text context available to cross-examine.", 
            "exact_evidence_quotes": [], 
            "counter_arguments_found": "N/A"
        }

    chunks_text = "\n\n---\n\n".join(
        f"[Chunk {i+1} | {c['source']}]\n{c['text'][:1000]}"
        for i, c in enumerate(chunks[:6])
    )

    llm = get_llm(temperature=0.2, max_tokens=800)
    prompt = f"Student Claim/Question: {claim}\n\nResearch Paper Context:\n{chunks_text}"

    try:
        resp = await llm.ainvoke([
            ("system", SYSTEM_CROSS_EXAMINER),
            ("human", prompt)
        ])
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.content.strip(), flags=re.MULTILINE).strip()
        return json.loads(text)
    except Exception:
        return {
            "verdict": "UNADDRESSED",
            "confidence_score": 0.5,
            "verdict_explanation": "The cross-examination engine timed out or experienced formatting variations during evaluation.",
            "exact_evidence_quotes": [],
            "counter_arguments_found": "N/A"
        }


async def synthesize_multiple_papers(papers_data: List[Dict]) -> Dict:
    """
    Accepts a list of papers, where each element is structured as:
    {"title": "Paper Name", "chunks": [...]}
    Generates a comparative matrix, extraction of thematic alignments, contradictions, and unresolved gaps.
    """
    if not papers_data:
        return {"error": "No paper documents provided for literature synthesis."}

    # Compile the cross-document matrix context cleanly for the prompt context
    compiled_context = ""
    for idx, paper in enumerate(papers_data):
        title = paper.get("title", f"Paper_{idx+1}")
        chunks = paper.get("chunks", [])
        
        # Take up to 4 dense chunks per paper to keep context windows safe and relevant
        paper_text = "\n".join([f"- {c.get('text', '')[:700]}" for c in chunks[:4]])
        compiled_context += f"=== DOCUMENT {idx+1}: {title} ===\n{paper_text}\n\n"

    llm = get_llm(temperature=0.2, max_tokens=1800)
    prompt = f"Perform an aggressive cross-comparative synthesis on the following documents:\n\n{compiled_context}"

    try:
        resp = await llm.ainvoke([
            ("system", SYSTEM_SYNTHESIZER),
            ("human", prompt)
        ])
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.content.strip(), flags=re.MULTILINE).strip()
        return json.loads(text)
    except Exception as e:
        return {
            "synthesis_overview": f"A processing error occurred during structural literature parsing: {str(e)}",
            "comparative_matrix": [],
            "structural_alignments": [],
            "divergences_and_contradictions": [],
            "unresolved_research_gaps": ["Unable to map out gaps due to parsing safety defaults."]
        }