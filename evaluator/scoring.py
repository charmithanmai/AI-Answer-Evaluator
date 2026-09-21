WEIGHTS = {
    "correctness": 0.40,
    "relevance": 0.20,
    "completeness": 0.20,
    "semantic_similarity": 0.10,
    "concept_coverage": 0.10,
}


def aggregate(correctness, relevance, completeness, semantic_similarity, concept_coverage) -> float:
    """Rubric scores are 0-10. Similarity and coverage are 0-1, so scale them by 10."""
    score = (
        WEIGHTS["correctness"] * correctness
        + WEIGHTS["relevance"] * relevance
        + WEIGHTS["completeness"] * completeness
        + WEIGHTS["semantic_similarity"] * (semantic_similarity * 10)
        + WEIGHTS["concept_coverage"] * (concept_coverage * 10)
    )
    return round(score, 2)