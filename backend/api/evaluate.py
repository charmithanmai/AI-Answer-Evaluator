import traceback

from fastapi import APIRouter, HTTPException

from backend.schemas.evaluation import EvaluationRequest, EvaluationResponse
from backend.database import save_evaluation
router = APIRouter()

# Keep True while testing the UI. On Day 6 this becomes False.
USE_MOCK = False

EXPECTED_KEYS = [
    "correctness",
    "relevance",
    "completeness",
    "semantic_similarity",
    "concept_coverage",
    "overall_score",
    "feedback",
]


def mock_evaluation(question: str, reference_answer: str, ai_answer: str) -> dict:
    """Fake result used until the real evaluator is connected."""
    return {
        "correctness": 8,
        "relevance": 9,
        "completeness": 7,
        "semantic_similarity": 0.86,
        "concept_coverage": 0.75,
        "concepts_covered": 3,
        "concepts_total": 4,
        "missing_concepts": ["No preemption"],
        "overall_score": 8.1,
        "feedback": "The answer is mostly correct but misses an important concept.",
    }


def real_evaluation(question: str, reference_answer: str, ai_answer: str) -> dict:
    """Member 1's real evaluator."""
    # Imported here so the server still starts even if the evaluator
    # libraries are not installed yet.
    from evaluator.core import evaluate_answer

    return evaluate_answer(question, reference_answer, ai_answer)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def to_count(value):
    """Accept either a number or a list and return a whole number."""
    if isinstance(value, (list, tuple, set)):
        return len(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_result(raw: dict) -> dict:
    """Check the evaluator output and keep every value in a sensible range."""
    missing = [key for key in EXPECTED_KEYS if key not in raw]
    if missing:
        raise ValueError("Evaluator result is missing these keys: " + ", ".join(missing))

    result = dict(raw)

    # If concept coverage arrives as a percentage (e.g. 75), convert it to 0.75
    if float(result["concept_coverage"]) > 1:
        result["concept_coverage"] = float(result["concept_coverage"]) / 100

    for key in ["correctness", "relevance", "completeness", "overall_score"]:
        result[key] = round(clamp(result[key], 0, 10), 1)

    result["semantic_similarity"] = round(clamp(result["semantic_similarity"], 0, 1), 2)
    result["concept_coverage"] = round(clamp(result["concept_coverage"], 0, 1), 2)
    result["feedback"] = str(result["feedback"])

    result["concepts_covered"] = to_count(raw.get("concepts_covered"))
    result["concepts_total"] = to_count(raw.get("concepts_total"))

    missing_concepts = raw.get("missing_concepts") or []
    if isinstance(missing_concepts, (list, tuple, set)):
        result["missing_concepts"] = [str(item) for item in missing_concepts]
    else:
        result["missing_concepts"] = [str(missing_concepts)]

    return result


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate(request: EvaluationRequest):
    try:
        if USE_MOCK:
            raw = mock_evaluation(request.question, request.reference_answer, request.ai_answer)
        else:
            raw = real_evaluation(request.question, request.reference_answer, request.ai_answer)
        result = normalize_result(raw)
    except Exception as error:
        traceback.print_exc()  # full error appears in the server terminal
        raise HTTPException(status_code=500, detail="Evaluation failed: " + str(error))

    # Saving to history must never break an evaluation
    try:
        save_evaluation(request.question, request.reference_answer, request.ai_answer, result)
    except Exception:
        traceback.print_exc()

    return result
