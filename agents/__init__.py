from .darban import classify
from .mehakkim import validate
from .ustad import stream_answer
from .imtehaan import start_quiz, evaluate_answer
from .muhaqqiq import analyze_paper, cross_examine_claim, synthesize_multiple_papers

__all__ = [
    "classify",
    "validate",
    "stream_answer",
    "start_quiz",
    "evaluate_answer",
    "analyze_paper",
    "cross_examine_claim",
    "synthesize_multiple_papers"
]
