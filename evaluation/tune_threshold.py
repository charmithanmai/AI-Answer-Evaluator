"""Tune Member 1's concept-coverage threshold (SIM_THRESHOLD = 0.55, a first guess
from 5 test cases) against the human completeness scores. No API calls.

    python -m evaluation.tune_threshold

Writes results/threshold_tuning.csv. Send the best value to Member 1 as a
finding. If she changes SIM_THRESHOLD, delete results/system_scores.csv and
re-run run_experiments so the hybrid scores use the new threshold.
"""
import pandas as pd

import evaluator.concepts as concepts
from evaluation.metrics import mae, pearson, spearman


def main():
    ans = pd.read_csv("data/answers.csv").merge(pd.read_csv("data/questions.csv"), on="question_id")
    h = pd.read_csv("data/human_scores.csv").groupby("answer_id").completeness.mean()
    ans = ans[ans.answer_id.isin(h.index)]
    y = h.loc[ans.answer_id].values

    original = concepts.SIM_THRESHOLD
    rows = []
    for t in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75]:
        concepts.SIM_THRESHOLD = t
        cov = [concepts.concept_coverage(r.reference_answer, r.ai_answer)["coverage"] * 10
               for r in ans.itertuples()]
        rows.append({"threshold": t, "MAE vs human completeness": mae(y, cov),
                     "Pearson": pearson(y, cov), "Spearman": spearman(y, cov)})
        print(rows[-1])
    concepts.SIM_THRESHOLD = original

    df = pd.DataFrame(rows).round(3)
    df.to_csv("results/threshold_tuning.csv", index=False)
    best = df.loc[df.Spearman.idxmax()]
    print(f"\nCurrent threshold {original}. Best by Spearman: {best.threshold} "
          f"(Spearman {best.Spearman}, MAE {best['MAE vs human completeness']})")


if __name__ == "__main__":
    main()
