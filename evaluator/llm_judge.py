def llm_rubric_evaluate(question: str, reference: str, ai_answer: str) -> dict:
    """STUB. Real version on Day 5."""
    return {
        "correctness": 8,
        "relevance": 9,
        "completeness": 6,
        "feedback": "Explains the main idea but omits some required conditions.",
    }