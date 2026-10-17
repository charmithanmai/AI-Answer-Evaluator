"""Baseline 3 — LLM-only evaluator.

Same Gemini model, same client, same rate limiter and same JSON parsing as
Member 1's llm_judge.py. The difference: ONE plain prompt asking for ONE
holistic 0-10 score — no rubric breakdown, no concept coverage, no embeddings.
"""
import time

from evaluator.preprocessing import clean_text
from evaluator.llm_judge import (MODEL_NAME, _get_client, _wait_for_slot,
                                 _parse_json_response, _clean_score)

PROMPT = """You are grading a student's answer against a reference answer.

Question: {question}

Reference answer: {reference}

Student's answer: {ai_answer}

Give ONE overall score from 0 to 10 for how well the student's answer matches the reference.
Respond with ONLY valid JSON, no other text, in exactly this shape:
{{"score": <0-10>}}
"""


def llm_score(question: str, reference_answer: str, ai_answer: str, retries: int = 3):
    """Returns a 0-10 float, or None if every attempt failed (so we can re-run it later)."""
    client = _get_client()
    prompt = PROMPT.format(question=clean_text(question),
                           reference=clean_text(reference_answer),
                           ai_answer=clean_text(ai_answer))
    for attempt in range(retries):
        try:
            _wait_for_slot()
            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            return round(_clean_score(_parse_json_response(response.text)["score"]), 2)
        except Exception as e:
            print(f"  LLM baseline attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
    return None
