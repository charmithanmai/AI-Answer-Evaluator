from sentence_transformers import SentenceTransformer, util

_model = None


def _get_model():
    """Load the model once, on first use, and reuse it after that."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def semantic_similarity(reference: str, ai_answer: str) -> float:
    """Cosine similarity between the two answers, clamped to 0-1."""
    if not reference or not ai_answer:
        return 0.0
    model = _get_model()
    embeddings = model.encode([reference, ai_answer], convert_to_tensor=True)
    score = util.cos_sim(embeddings[0], embeddings[1]).item()
    return max(0.0, min(1.0, score))