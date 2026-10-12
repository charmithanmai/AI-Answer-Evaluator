import json
import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL_NAME = "gemini-3.8-flash"  # one place to change if Google renames it again
_client = None

RUBRIC_PROMPT = """You are grading a student's answer against a reference answer.

Question: {question}

Reference answer: {reference}

Student's answer: {ai_answer}

Score the student's answer from 0 to 10 on each of these:
- correctness: factual accuracy compared to the reference
- relevance: does it address the question asked
- completeness: does it cover what the reference covers

Then write one short sentence of feedback explaining the biggest gap or error.

Respond with ONLY valid JSON, no other text, in exactly this shape:
{{"correctness": <0-10>, "relevance": <0-10>, "completeness": <0-10>, "feedback": "<one sentence>"}}
"""


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not found. Check your .env file.")
        _client = genai.Client(api_key=api_key)
    return _client


def _parse_json_response(text: str) -> dict:
    """The model sometimes wraps JSON in ```json fences. Strip those if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def llm_rubric_evaluate(question: str, reference: str, ai_answer: str, retries: int = 3) -> dict:
    """Ask the LLM to score the answer. Retries on temporary server errors."""
    client = _get_client()
    prompt = RUBRIC_PROMPT.format(question=question, reference=reference, ai_answer=ai_answer)

    last_error = None
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            result = _parse_json_response(response.text)
            # make sure all expected keys are present
            for key in ("correctness", "relevance", "completeness", "feedback"):
                if key not in result:
                    raise ValueError(f"Missing key in LLM response: {key}")
            return result
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))  # wait longer each retry: 5s, 10s
            continue

    # all retries failed — return a safe fallback instead of crashing the whole pipeline
    return {
        "correctness": 0,
        "relevance": 0,
        "completeness": 0,
        "feedback": f"LLM evaluation failed after {retries} attempts: {last_error}",
    }