from typing import List, Optional

from pydantic import BaseModel, field_validator


class EvaluationRequest(BaseModel):
    question: str
    reference_answer: str
    ai_answer: str

    @field_validator("question", "reference_answer", "ai_answer")
    @classmethod
    def must_not_be_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field must not be empty")
        return value


class EvaluationResponse(BaseModel):
    correctness: float
    relevance: float
    completeness: float
    semantic_similarity: float
    concept_coverage: float
    overall_score: float
    feedback: str
    # Extra details from Member 1's evaluator
    concepts_covered: Optional[int] = None
    concepts_total: Optional[int] = None
    missing_concepts: List[str] = []