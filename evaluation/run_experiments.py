"""Run ALL four evaluators on the SAME 90 answers and save the scores.

    python -m evaluation.run_experiments                 # everything (needs Gemini)
    python -m evaluation.run_experiments --offline       # keyword + semantic only (no API)
    python -m evaluation.run_experiments --limit 3       # quick test on 3 answers

Output: results/system_scores.csv (one row per answer).
Resumable: re-running only fills in what is missing or failed, so a quota
error or a closed laptop does not cost you the finished rows.

GEMINI COST: 1 call per answer (90 total).
  The hybrid evaluator makes one rubric call (correctness, relevance,
  completeness). The LLM-only baseline is computed from that SAME call:
      llm_only = 0.50*correctness + 0.25*relevance + 0.25*completeness
  i.e. the hybrid's own rubric weights (0.4/0.2/0.2) rescaled to sum to 1.
  So "LLM-only" vs "Hybrid" differ ONLY by adding semantic similarity and
  concept coverage — a clean comparison, and half the API calls.
  (--separate-llm-call uses the old separate one-score prompt instead: 180 calls.)

FREE-TIER KEYS: the free tier allows 20 calls/day per Google project.
  Put several teammates' keys in .env and the script switches to the next
  key when one runs out:
      GEMINI_API_KEY=first_key
      GEMINI_API_KEY_2=second_key
      GEMINI_API_KEY_3=third_key
  When every key is used up it stops cleanly; run it again the next day.
"""
import argparse
import json
import os

import pandas as pd
from dotenv import load_dotenv

from baselines.keyword import keyword_score
from baselines.semantic_baseline import semantic_score

OUT = "results/system_scores.csv"
HYBRID_COLS = ["correctness", "relevance", "completeness", "semantic_similarity",
               "concept_coverage", "concepts_covered", "concepts_total",
               "missing_concepts", "overall_score", "feedback"]
LAST = {}
FAILED_MARKS = ("LLM evaluation failed", "AI judge was unavailable")
LLM_ONLY_WEIGHTS = {"correctness": 0.50, "relevance": 0.25, "completeness": 0.25}


def _blank(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or v == ""


def _save(rows, prev):
    done = {r["answer_id"] for r in rows}
    keep = [dict(v, answer_id=k) for k, v in prev.items() if k not in done]
    pd.DataFrame(rows + keep).sort_values("answer_id").to_csv(OUT, index=False)


def _llm_only_from_rubric(row):
    return round(sum(w * float(row[c]) for c, w in LLM_ONLY_WEIGHTS.items()), 2)


def _load_keys():
    load_dotenv()
    names = ["GEMINI_API_KEY"] + [f"GEMINI_API_KEY_{i}" for i in range(2, 10)]
    return [os.environ[n] for n in names if os.environ.get(n)]


def _is_quota_error(text):
    t = str(text)
    return "429" in t or "RESOURCE_EXHAUSTED" in t or "quota" in t.lower()


class KeyRing:
    """Switches Member 1's Gemini client to the next key when one hits its daily quota."""

    def __init__(self, keys):
        self.keys, self.i = keys, 0
        self._use(0)

    def _use(self, i):
        import evaluator.llm_judge as judge
        os.environ["GEMINI_API_KEY"] = self.keys[i]
        judge._client = None  # force M1's judge to build a new client with this key

    def next(self):
        self.i += 1
        if self.i >= len(self.keys):
            return False
        print(f"  -> switching to Gemini key #{self.i + 1}")
        self._use(self.i)
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="skip the Gemini-based methods")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--separate-llm-call", action="store_true",
                    help="LLM-only baseline with its own prompt (doubles API calls)")
    args = ap.parse_args()

    answers = pd.read_csv("data/answers.csv")
    qs = pd.read_csv("data/questions.csv")
    df = answers.merge(qs, on="question_id").sort_values("answer_id")
    if args.limit:
        df = df.head(args.limit)

    os.makedirs("results", exist_ok=True)
    prev = pd.read_csv(OUT).set_index("answer_id").to_dict("index") if os.path.exists(OUT) else {}

    online = not args.offline
    if online:
        keys = _load_keys()
        if not keys:
            raise SystemExit("No GEMINI_API_KEY found in .env")
        print(f"Using {len(keys)} Gemini key(s).")
        ring = KeyRing(keys)
        from evaluator import evaluate_answer
        import evaluator.core as core
        _judge = core.llm_rubric_evaluate

        def _spy(*a, **k):  # remember the judge's raw message (M1's feedback hides errors)
            k.setdefault("retries", 1)  # 1 try per call: retries on 503 also use up the daily quota
            res = _judge(*a, **k)
            LAST["judge_feedback"] = res["feedback"]
            return res
        core.llm_rubric_evaluate = _spy
        if args.separate_llm_call:
            from baselines.llm_baseline import llm_score

    rows, out_of_quota, overload_streak = [], False, 0
    for _, r in df.iterrows():
        row = dict(prev.get(r.answer_id, {}))
        row.update(answer_id=r.answer_id, question_id=r.question_id, topic=r.topic,
                   category=r.category)

        row["keyword_score"] = keyword_score(r.reference_answer, r.ai_answer)
        row["semantic_score"] = semantic_score(r.reference_answer, r.ai_answer)

        if online and not out_of_quota:
            failed_before = any(m in str(row.get("feedback", "")) for m in FAILED_MARKS)
            if _blank(row.get("overall_score")) or failed_before:
                while True:
                    LAST.clear()
                    res = evaluate_answer(r.question, r.reference_answer, r.ai_answer)
                    fb = LAST.get("judge_feedback", "")
                    if not fb.startswith("LLM evaluation failed"):
                        res["missing_concepts"] = json.dumps(res["missing_concepts"])
                        row.update({k: res[k] for k in HYBRID_COLS})
                        overload_streak = 0
                        break
                    row.update({k: None for k in HYBRID_COLS + ["llm_only_score"]})  # never keep fallback zeros
                    if _is_quota_error(fb) and ring.next():
                        continue  # retry this answer with the next key
                    if _is_quota_error(fb):
                        out_of_quota = True
                        print("\nAll Gemini keys have used today's free quota. "
                              "Progress is saved. Run the same command again tomorrow.")
                    else:
                        print(f"  A{r.answer_id}: Gemini failed ({fb[:80]}...) — left blank, re-run later")
                        overload_streak += 1
                        if overload_streak >= 2:
                            out_of_quota = True  # stop calling Gemini for this run
                            print("\nGemini keeps failing (503 = Google's servers are overloaded). "
                                  "Stopping now so retries don't waste your daily quota.\n"
                                  "Progress is saved. Try the same command again in an hour or two.")
                    break

            if not _blank(row.get("overall_score")):
                if args.separate_llm_call:
                    if _blank(row.get("llm_only_score")):
                        row["llm_only_score"] = llm_score(r.question, r.reference_answer, r.ai_answer)
                else:
                    row["llm_only_score"] = _llm_only_from_rubric(row)

        rows.append(row)
        _save(rows, prev)  # save after every answer
        print(f"A{r.answer_id:>3} {r.category:<20} kw={row['keyword_score']:<5} "
              f"sem={row['semantic_score']:<5} llm={row.get('llm_only_score')} "
              f"hybrid={row.get('overall_score')}")

    out = pd.read_csv(OUT)
    if online:
        if "overall_score" not in out:
            out["overall_score"] = None
        left = int(out.overall_score.isna().sum())
        if left:
            print(f"\n{len(out) - left}/{len(out)} answers have Gemini scores; {left} still to do. "
                  "Run the same command again (tomorrow if quota is used up).")
        else:
            print(f"\nAll {len(out)} answers scored by all 4 methods -> {OUT}")


if __name__ == "__main__":
    main()
