from evaluator.preprocessing import clean_text
from evaluator.semantic import semantic_similarity
from evaluator.concepts import concept_coverage
from evaluator.llm_judge import llm_rubric_evaluate
from evaluator.scoring import aggregate
from evaluator.feedback import build_feedback


def evaluate_answer(question: str, reference_answer: str, ai_answer: str) -> dict:
    q = clean_text(question)
    ref = clean_text(reference_answer)
    ans = clean_text(ai_answer)

    sim = semantic_similarity(ref, ans)
    cov = concept_coverage(ref, ans)
    rubric = llm_rubric_evaluate(q, ref, ans)

    overall = aggregate(
        rubric["correctness"],
        rubric["relevance"],
        rubric["completeness"],
        sim,
        cov["coverage"],
    )

    return {
        "correctness": rubric["correctness"],
        "relevance": rubric["relevance"],
        "completeness": rubric["completeness"],
        "semantic_similarity": round(sim, 3),
        "concept_coverage": round(cov["coverage"], 3),
        "concepts_covered": cov["covered"],
        "concepts_total": cov["total"],
        "missing_concepts": cov["missing"],
        "overall_score": overall,
        "feedback": build_feedback(rubric["feedback"], cov["missing"],overall),
    }