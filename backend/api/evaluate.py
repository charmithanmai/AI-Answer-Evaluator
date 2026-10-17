from fastapi import APIRouter

from backend.schemas.evaluation import EvaluationRequest, EvaluationResponse

router = APIRouter()


def run_evaluation(question: str, reference_answer: str, ai_answer: str) -> dict:
    """
    TEMPORARY mock evaluator.
    On Day 6 this function will call Member 1's real evaluate_answer().
    """
    return {
        "correctness": 8,
        "relevance": 9,
        "completeness": 7,
        "semantic_similarity": 0.86,
        "concept_coverage": 0.75,
        "overall_score": 8.1,
        "feedback": "The answer is mostly correct but misses an important concept.",
    }


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate(request: EvaluationRequest):
    result = run_evaluation(
        question=request.question,
        reference_answer=request.reference_answer,
        ai_answer=request.ai_answer,
    )
    return result