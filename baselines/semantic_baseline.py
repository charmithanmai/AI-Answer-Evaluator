"""Baseline 2 — Semantic-only evaluator.

Reuses Member 1's semantic_similarity() (all-MiniLM-L6-v2, cosine, clamped 0-1)
so the ONLY difference from the hybrid system is "embeddings alone".
Score = similarity x 10.
"""
from evaluator.preprocessing import clean_text
from evaluator.semantic import semantic_similarity


def semantic_score(reference_answer: str, ai_answer: str) -> float:
    sim = semantic_similarity(clean_text(reference_answer), clean_text(ai_answer))
    return round(sim * 10, 2)


if __name__ == "__main__":
    ref = "Deadlock occurs when processes wait indefinitely for resources held by each other."
    ans = "Deadlock is when two or more processes wait for resources held by one another."
    print("semantic score:", semantic_score(ref, ans))
