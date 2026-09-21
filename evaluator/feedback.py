def build_feedback(llm_feedback: str, missing_concepts: list) -> str:
    """STUB. Real version on Day 7."""
    text = llm_feedback or ""
    if missing_concepts:
        text += " Missing concepts: " + ", ".join(missing_concepts) + "."
    return text.strip()