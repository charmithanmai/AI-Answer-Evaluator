"""Baseline 1 — Keyword / lexical overlap evaluator.

Uses EXACTLY the same keyword rules as Member 1's concept module
(evaluator/concepts.py): same stopword list (keeps "no"/"not"), same
tokenizer, same loose word match ("wait" ~ "waiting", "resource" ~ "resources").

Score = F1 of keyword overlap between reference and AI answer, scaled 0-10.
(Recall alone would reward long rambling answers; F1 balances that.)
"""
from evaluator.preprocessing import clean_text
from evaluator.concepts import _content_tokens, _same_word


def _matched(source: list, target: list) -> int:
    return sum(any(_same_word(w, t) for t in target) for w in source)


def keyword_score(reference_answer: str, ai_answer: str) -> float:
    ref = list(dict.fromkeys(_content_tokens(clean_text(reference_answer))))
    ans = list(dict.fromkeys(_content_tokens(clean_text(ai_answer))))
    if not ref or not ans:
        return 0.0
    recall = _matched(ref, ans) / len(ref)
    precision = _matched(ans, ref) / len(ans)
    if recall + precision == 0:
        return 0.0
    f1 = 2 * precision * recall / (precision + recall)
    return round(f1 * 10, 2)


if __name__ == "__main__":
    ref = ("Deadlock occurs when processes wait indefinitely for resources held by each other. "
           "It requires mutual exclusion, hold and wait, no preemption, and circular wait.")
    ans = "Deadlock occurs when two or more processes wait for resources held by one another, so none can proceed."
    print("keyword score:", keyword_score(ref, ans))
