"""Run ALL four evaluators on the SAME 90 answers and save the scores.

    python -m evaluation.run_experiments                 # everything (needs Gemini)
    python -m evaluation.run_experiments --offline       # keyword + semantic only (no API)
    python -m evaluation.run_experiments --limit 3       # quick test on 3 answers

Output: results/system_scores.csv (one row per answer).
Resumable: re-running only fills in what is missing or failed, so a quota
error or a closed laptop does not cost you the finished rows.

Gemini cost: 2 calls per answer (hybrid judge + LLM-only baseline).
At Member 1's rate limit (6.5 s/call) 90 answers take about 20 minutes.
"""
import argparse
import json
import os

import pandas as pd

from baselines.keyword import keyword_score
from baselines.semantic_baseline import semantic_score

OUT = "results/system_scores.csv"
HYBRID_COLS = ["correctness", "relevance", "completeness", "semantic_similarity",
               "concept_coverage", "concepts_covered", "concepts_total",
               "missing_concepts", "overall_score", "feedback"]


def _blank(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or v == ""


def _save(rows, prev):
    done = {r["answer_id"] for r in rows}
    keep = [dict(v, answer_id=k) for k, v in prev.items() if k not in done]
    pd.DataFrame(rows + keep).sort_values("answer_id").to_csv(OUT, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="skip the two Gemini-based methods")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    answers = pd.read_csv("data/answers.csv")
    qs = pd.read_csv("data/questions.csv")
    df = answers.merge(qs, on="question_id").sort_values("answer_id")
    if args.limit:
        df = df.head(args.limit)

    os.makedirs("results", exist_ok=True)
    prev = pd.read_csv(OUT).set_index("answer_id").to_dict("index") if os.path.exists(OUT) else {}

    if not args.offline:
        from evaluator import evaluate_answer
        from baselines.llm_baseline import llm_score

    rows = []
    for _, r in df.iterrows():
        row = dict(prev.get(r.answer_id, {}))
        row.update(answer_id=r.answer_id, question_id=r.question_id, topic=r.topic,
                   category=r.category)

        row["keyword_score"] = keyword_score(r.reference_answer, r.ai_answer)
        row["semantic_score"] = semantic_score(r.reference_answer, r.ai_answer)

        if not args.offline:
            if _blank(row.get("llm_only_score")):
                row["llm_only_score"] = llm_score(r.question, r.reference_answer, r.ai_answer)

            failed_before = str(row.get("feedback", "")).startswith("LLM evaluation failed")
            if _blank(row.get("overall_score")) or failed_before:
                res = evaluate_answer(r.question, r.reference_answer, r.ai_answer)
                if res["feedback"].startswith("LLM evaluation failed"):
                    print(f"  A{r.answer_id}: Gemini failed — left blank, re-run later")
                    res = {k: None for k in HYBRID_COLS}
                else:
                    res["missing_concepts"] = json.dumps(res["missing_concepts"])
                row.update({k: res[k] for k in HYBRID_COLS})

        rows.append(row)
        _save(rows, prev)  # save after every answer
        print(f"A{r.answer_id:>3} {r.category:<20} kw={row['keyword_score']:<5} "
              f"sem={row['semantic_score']:<5} llm={row.get('llm_only_score')} "
              f"hybrid={row.get('overall_score')}")

    out = pd.read_csv(OUT)
    if not args.offline:
        todo = out[out.overall_score.isna() | out.llm_only_score.isna()]
        if len(todo):
            print(f"\n{len(todo)} answers still incomplete. Run the same command again.")
        else:
            print(f"\nAll {len(out)} answers scored by all 4 methods -> {OUT}")


if __name__ == "__main__":
    main()
