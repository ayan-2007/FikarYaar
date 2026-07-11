"""
RAG evaluation harness.

Run:
    python scripts/eval_rag.py --mode retrieval   # no LLM key needed
    python scripts/eval_rag.py --mode full        # full pipeline incl. generation
    python scripts/eval_rag.py --rebuild          # wipe + re-ingest then eval
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# Allow running as `python scripts/eval_rag.py`
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.rag.graph import ask  # noqa: E402
from app.rag.ingest import ingest_all_sources  # noqa: E402
from app.rag.vectorstore import collection_count, retrieve_with_threshold  # noqa: E402


@dataclass
class EvalCase:
    question: str
    category: str
    expect_answer: bool  # False = should refuse / no notes


EVAL_SET: list[EvalCase] = [
    EvalCase("What is a class?", "factual", True),
    EvalCase("What are relationships between classes?", "section", True),
    EvalCase("What is dynamic cast used for?", "precision_trap", False),
    EvalCase("What is a structure in C++?", "factual", True),
    EvalCase("What is operator overloading?", "factual", True),
    EvalCase("What is the diamond problem in C++?", "section", True),
    EvalCase("What is the rule of five?", "factual", True),
    EvalCase("What is a vtable?", "factual", True),
    EvalCase("What is polymorphism in C++?", "factual", True),
    EvalCase("What is the difference between composition and aggregation?", "section", True),
    EvalCase("What is move semantics?", "factual", True),
    EvalCase("What is shallow copy versus deep copy?", "factual", True),
    EvalCase("What is a POD type?", "factual", True),
    EvalCase("How do constructors and destructors work in inheritance?", "section", True),
    EvalCase("What is static dispatch versus dynamic dispatch?", "factual", True),
    EvalCase("What is the capital of France?", "refusal", False),
    EvalCase("Who won the FIFA World Cup in 2022?", "refusal", False),
    EvalCase("Write me a poem about spring flowers", "offtopic", False),
    EvalCase("What is the cookie cutter metaphor in object-oriented programming?", "gaddis_specific", True),
    EvalCase("What is RTTI and run-time type identification?", "factual", True),
]


def _retrieval_eval() -> list[dict]:
    rows = []
    for case in EVAL_SET:
        scored = retrieve_with_threshold(case.question)
        rows.append(
            {
                "question": case.question,
                "category": case.category,
                "expect_answer": case.expect_answer,
                "retrieved": len(scored),
                "top_chunks": [
                    {
                        "score": round(score, 4),
                        "source": doc.metadata.get("source_name"),
                        "section": doc.metadata.get("section"),
                        "preview": doc.page_content[:140].replace("\n", " "),
                    }
                    for doc, score in scored[:3]
                ],
            }
        )
    return rows


def _full_eval() -> list[dict]:
    rows = []
    for case in EVAL_SET:
        result = ask(case.question, [])
        rows.append(
            {
                "question": case.question,
                "category": case.category,
                "expect_answer": case.expect_answer,
                "used_notes": result.get("used_notes", False),
                "answer": result.get("answer", "")[:500],
                "sources": result.get("sources", []),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline quality")
    parser.add_argument(
        "--mode",
        choices=["retrieval", "full"],
        default="retrieval",
        help="retrieval = scores only; full = end-to-end answers",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Wipe vector DB and re-ingest all sources before eval",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "eval_results.json",
        help="Where to write JSON results",
    )
    args = parser.parse_args()

    if args.rebuild:
        summary = ingest_all_sources()
        print(f"Rebuilt index: {summary}")

    print(f"Chunks in store: {collection_count()}")
    print(f"Settings: top_k={settings.top_k} candidates={settings.retrieval_candidate_k} "
          f"max_distance={settings.retrieval_max_distance} "
          f"chunk_tokens={settings.chunk_size_tokens}")

    if args.mode == "retrieval":
        results = _retrieval_eval()
    else:
        results = _full_eval()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {len(results)} cases to {args.out}")

    # Quick summary
    if args.mode == "retrieval":
        answered = sum(1 for r in results if r["retrieved"] > 0)
        refused_retrieval = len(results) - answered
        print(f"Retrieval passed threshold: {answered}/{len(results)} "
              f"(no match: {refused_retrieval})")
    else:
        used = sum(1 for r in results if r["used_notes"])
        print(f"Pipeline used notes: {used}/{len(results)}")


if __name__ == "__main__":
    main()
