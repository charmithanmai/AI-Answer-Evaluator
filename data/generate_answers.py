"""Generate ~90 AI answers (30 questions x 3 quality categories) with Gemini.

Uses Member 1's Gemini client + rate limiter, so it needs the same .env
(GEMINI_API_KEY). Safe to stop and re-run: finished answers are kept.

    python -m data.generate_answers

After it finishes, OPEN data/answers.csv AND READ EVERY ANSWER. If an answer
does not match its category (e.g. "hallucinated" but actually correct),
edit it by hand. A wrong label silently ruins the per-category analysis.
"""
import os
import time

import pandas as pd

from evaluator.llm_judge import MODEL_NAME, _get_client, _wait_for_slot

QUESTIONS = "data/questions.csv"
OUT = "data/answers.csv"

CATEGORIES = {
    "fully_correct": "Write a complete and correct answer that covers every point in the reference.",
    "mostly_correct": "Write a correct answer that covers most points in the reference but leaves out one minor point.",
    "partially_correct": "Write an answer where about half the points are correct and the rest are missing or vague.",
    "correct_incomplete": "Write a correct answer that explains only the main idea in one sentence and skips all the details.",
    "relevant_incorrect": "Write an answer that stays on the topic and sounds confident, but states the main idea INCORRECTLY.",
    "irrelevant": "Write a fluent answer about a DIFFERENT topic in the same subject that does not answer the question.",
    "paraphrased_correct": "Write a fully correct answer that covers every point but uses completely different wording from the reference, with synonyms and different sentence structure.",
    "hallucinated": "Write an answer that is mostly correct but adds one or two made-up facts that sound plausible but are false.",
    "very_short": "Write a correct answer in at most 8 words.",
    "overly_verbose": "Write a correct answer that covers every point but is padded with unnecessary repetition and filler, about 150 words.",
}
CAT_NAMES = list(CATEGORIES)

PROMPT = """You are helping build a test dataset for an answer-grading system.

Question: {question}
Reference answer: {reference}

Instruction: {instruction}

Write ONLY the answer text, as a student would write it. No labels, no notes, no markdown."""


def main():
    qs = pd.read_csv(QUESTIONS)
    done = pd.read_csv(OUT) if os.path.exists(OUT) else pd.DataFrame(
        columns=["answer_id", "question_id", "category", "ai_answer"])
    rows = done.to_dict("records")
    have = {(r["question_id"], r["category"]) for r in rows}
    client = _get_client()

    answer_id = len(rows)
    for i, q in qs.iterrows():
        # 3 categories per question, rotating so each category appears ~9 times
        for k in range(3):
            cat = CAT_NAMES[(3 * i + k) % len(CAT_NAMES)]
            if (q.question_id, cat) in have:
                continue
            prompt = PROMPT.format(question=q.question, reference=q.reference_answer,
                                   instruction=CATEGORIES[cat])
            for attempt in range(3):
                try:
                    _wait_for_slot()
                    text = client.models.generate_content(model=MODEL_NAME, contents=prompt).text.strip()
                    break
                except Exception as e:
                    print("  retry:", e)
                    time.sleep(5 * (attempt + 1))
            else:
                print(f"SKIPPED {q.question_id} {cat} — run again later")
                continue
            answer_id += 1
            rows.append({"answer_id": answer_id, "question_id": q.question_id,
                         "category": cat, "ai_answer": " ".join(text.split())})
            pd.DataFrame(rows).to_csv(OUT, index=False)  # save after every answer
            print(f"A{answer_id:02d} {q.question_id} {cat}")

    df = pd.DataFrame(rows).sort_values(["question_id", "answer_id"])
    df["answer_id"] = range(1, len(df) + 1)
    df.to_csv(OUT, index=False)
    print(f"\nDone: {len(df)} answers in {OUT}")
    print(df.category.value_counts().to_string())


if __name__ == "__main__":
    main()
