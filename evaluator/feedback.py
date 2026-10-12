LLM_FAILED_PREFIX = "LLM evaluation failed"


def _band(score: float) -> str:
    if score >= 8.5:
        return "Excellent"
    if score >= 7:
        return "Good"
    if score >= 5:
        return "Partial"
    return "Weak"


def build_feedback(llm_feedback: str, missing_concepts: list, overall_score=None) -> str:
    """Combine the LLM comment, a quality band and the missing concepts into one text."""
    llm_feedback = (llm_feedback or "").strip()
    missing_concepts = missing_concepts or []
    llm_failed = llm_feedback.startswith(LLM_FAILED_PREFIX)

    parts = []
    if llm_failed:
        # the zero scores are not real, so don't show a band based on them
        parts.append("The AI judge was unavailable, so this feedback uses concept coverage only.")
    else:
        if overall_score is not None:
            parts.append(f"{_band(overall_score)} answer ({overall_score}/10).")
        if llm_feedback:
            parts.append(llm_feedback)

    if missing_concepts:
        parts.append("Missing concepts: " + ", ".join(missing_concepts) + ".")

    return " ".join(parts)