import re

from sentence_transformers import util

from evaluator.preprocessing import clean_text
from evaluator.semantic import _get_model

# Starting guess. We tune this from real results, not from theory.
SIM_THRESHOLD = 0.55

_LEAD_IN = re.compile(
    r"^(?:it|this|they|these)?\s*"
    r"(?:requires|needs|includes|involves|consists of|comprises|has|have)\s+"
    r"(?:the following\s+)?",
    re.IGNORECASE,
)
_LEADING_CONJ = re.compile(r"^(?:and|or|but|also)\s+", re.IGNORECASE)

# "no" and "not" are deliberately NOT here: "no preemption" must not match "preemption".
_STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "to", "for", "by", "is", "are", "be",
    "it", "its", "and", "or", "that", "this", "when", "each", "other", "with",
    "as", "at", "from", "can", "so", "which",
}


def extract_concepts(reference: str) -> list:
    """Split a reference answer into checkable concepts.

    Normal sentence -> one concept.
    List-like sentence (2+ commas or a semicolon) -> one concept per item.
    """
    text = clean_text(reference)
    if not text:
        return []

    concepts = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        sentence = sentence.strip().rstrip(".!?").strip()
        if not sentence:
            continue

        is_list = sentence.count(",") >= 2 or ";" in sentence
        if not is_list:
            concepts.append(sentence)
            continue

        for i, part in enumerate(re.split(r"[;,]", sentence)):
            part = _LEADING_CONJ.sub("", part.strip())
            if i == 0:
                part = _LEAD_IN.sub("", part)
            if len(part) > 2:
                concepts.append(part)

    unique, seen = [], set()
    for c in concepts:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique.append(c)
    return unique


def _content_tokens(text: str) -> list:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in _STOPWORDS]


def _same_word(a: str, b: str) -> bool:
    """Loose match so 'wait' matches 'waiting' and 'resource' matches 'resources'."""
    if a == b:
        return True
    if min(len(a), len(b)) < 4:
        return False
    k = min(len(a), len(b), 6)
    return a[:k] == b[:k]


def _lexical_match(concept_tokens: list, answer_tokens: list) -> bool:
    if not concept_tokens:
        return False
    return all(any(_same_word(c, a) for a in answer_tokens) for c in concept_tokens)


def _chunks(text: str) -> list:
    """Sentences, plus the comma/semicolon parts inside each sentence."""
    chunks = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        sentence = sentence.strip().rstrip(".!?").strip()
        if not sentence:
            continue
        chunks.append(sentence)
        parts = [p.strip() for p in re.split(r"[;,:]", sentence) if len(p.strip()) > 2]
        if len(parts) > 1:
            chunks.extend(parts)
    return chunks or [text]


def concept_coverage(reference: str, ai_answer: str) -> dict:
    """How many reference concepts does the AI answer cover?"""
    concepts = extract_concepts(reference)
    answer = clean_text(ai_answer)

    if not concepts:
        return {"covered": 0, "total": 0, "coverage": 0.0, "missing": [], "details": []}
    if not answer:
        return {
            "covered": 0,
            "total": len(concepts),
            "coverage": 0.0,
            "missing": list(concepts),
            "details": [],
        }

    answer_tokens = _content_tokens(answer)
    chunks = _chunks(answer)

    model = _get_model()
    concept_emb = model.encode(concepts, convert_to_tensor=True)
    chunk_emb = model.encode(chunks, convert_to_tensor=True)
    best_scores = util.cos_sim(concept_emb, chunk_emb).max(dim=1).values.tolist()

    details, missing = [], []
    for concept, best in zip(concepts, best_scores):
        if _lexical_match(_content_tokens(concept), answer_tokens):
            covered, method, score = True, "words", 1.0
        elif best >= SIM_THRESHOLD:
            covered, method, score = True, "meaning", best
        else:
            covered, method, score = False, "none", best
            missing.append(concept)
        details.append(
            {"concept": concept, "covered": covered, "method": method, "score": round(score, 3)}
        )

    covered_count = sum(d["covered"] for d in details)
    return {
        "covered": covered_count,
        "total": len(concepts),
        "coverage": covered_count / len(concepts),
        "missing": missing,
        "details": details,
    }