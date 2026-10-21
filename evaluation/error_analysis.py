"""Error analysis: where does an automated evaluator disagree with humans, and why?

    python -m evaluation.error_analysis

Needs results/merged.csv (run comparison.py first).
Writes results/error_analysis.md — a ready-to-edit draft for the report.

Which system is analysed:
  * the HYBRID evaluator, if at least 10 answers have Gemini scores;
  * otherwise the SEMANTIC baseline (with keyword for comparison), so the
    analysis still works before / without the Gemini run.
The 'likely cause' tags are automatic GUESSES. Read each case and correct them.
"""
import json
import sys

import pandas as pd

R = "results"
BIG = 2.0      # a disagreement of 2+ points (out of 10) counts as an error case
MIN_N = 10


def cause_hybrid(r) -> str:
    causes = []
    if r.overall_score > r.human_overall:
        if r.correctness >= 7 and r.human_correctness <= 4:
            causes.append("LLM judge believed fluent but wrong content")
        if r.semantic_similarity >= 0.75 and r.human_overall <= 5:
            causes.append("high semantic similarity on a weak answer (topic match, not truth)")
        if r.concept_coverage >= 0.6 and r.human_completeness <= 4:
            causes.append("concept coverage credited concepts that were only mentioned, not explained correctly")
        if r.category in ("hallucinated", "relevant_incorrect"):
            causes.append(f"'{r.category}' answer: false facts not penalized enough")
    else:
        if r.concept_coverage <= 0.4 and r.human_completeness >= 7:
            causes.append("concept extraction/matching missed concepts that WERE present (paraphrase)")
        if r.semantic_similarity <= 0.6 and r.human_overall >= 7:
            causes.append("low semantic similarity on a correct answer (different wording or length)")
        if r.completeness <= 4 and r.human_completeness >= 7:
            causes.append("LLM judge too strict on completeness")
        if r.category == "very_short":
            causes.append("short answer penalized more by the system than by humans")
    return "; ".join(causes) or "unclear — inspect manually"


def cause_semantic(r) -> str:
    causes = []
    if r.semantic_score > r.human_overall:
        if r.category in ("relevant_incorrect", "hallucinated"):
            causes.append("embedding measures topic overlap, not truth: wrong facts on the right topic score high")
        if r.human_completeness <= 4:
            causes.append("missing content is not detected: a partial answer is still 'similar' to the reference")
        if r.category == "irrelevant":
            causes.append("off-topic answer from the same subject area shares vocabulary with the reference")
    else:
        if r.category == "very_short":
            causes.append("very short answer has a weak embedding match even when correct")
        if r.category == "paraphrased_correct":
            causes.append("correct answer with different wording gets lower similarity")
    return "; ".join(causes) or "unclear — inspect manually"


def main():
    df = pd.read_csv(f"{R}/merged.csv")
    hybrid_mode = "overall_score" in df and df.overall_score.notna().sum() >= MIN_N
    if hybrid_mode:
        df = df.dropna(subset=["overall_score"]).copy()
        sys_col, name, cause = "overall_score", "Hybrid evaluator", cause_hybrid
    else:
        sys_col, name, cause = "semantic_score", "Semantic-only baseline", cause_semantic
        print("Gemini scores not available yet -> analysing the semantic baseline instead.")

    df["error"] = df[sys_col] - df.human_overall
    df["abs_error"] = df.error.abs()
    qs = pd.read_csv("data/questions.csv").set_index("question_id")
    ans = pd.read_csv("data/answers.csv").set_index("answer_id")

    big = df[df.abs_error >= BIG].sort_values("abs_error", ascending=False)
    over, under = big[big.error > 0], big[big.error < 0]

    L = [f"# Error Analysis — {name} vs human judgments", ""]
    L += [f"- Answers analysed: **{len(df)}**",
          f"- Large disagreements (|system − human| ≥ {BIG}): **{len(big)}** "
          f"({len(over)} over-scored, {len(under)} under-scored)"]
    if hybrid_mode and df.llm_only_score.notna().any():
        h_err = df.abs_error
        l_err = (df.llm_only_score - df.human_overall).abs()
        L.append(f"- Hybrid closer to humans than LLM-only (by >0.5 pt): **{(h_err < l_err - 0.5).sum()}** "
                 f"answers; LLM-only closer: **{(l_err < h_err - 0.5).sum()}** answers")
    else:
        k_err = (df.keyword_score - df.human_overall).abs()
        L.append(f"- Semantic closer to humans than keyword (by >0.5 pt): **{(df.abs_error < k_err - 0.5).sum()}** "
                 f"answers; keyword closer: **{(k_err < df.abs_error - 0.5).sum()}** answers")
    L.append("")

    L += ["## Error by category (mean signed error: + means system too generous)", "",
          "| Category | n | Human mean | System mean | Mean error | Mean |error| |",
          "|---|---|---|---|---|---|"]
    for c, g in df.groupby("category"):
        L.append(f"| {c} | {len(g)} | {g.human_overall.mean():.2f} | {g[sys_col].mean():.2f} | "
                 f"{g.error.mean():+.2f} | {g.abs_error.mean():.2f} |")
    L.append("")

    tags = big.apply(cause, axis=1)
    L += ["## Most frequent likely causes", ""]
    counts = {}
    for t in tags:
        for part in t.split("; "):
            counts[part] = counts.get(part, 0) + 1
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        L.append(f"- {k}: {v}")
    L.append("")

    L += ["## Individual cases", ""]
    for _, r in big.head(15).iterrows():
        q = qs.loc[r.question_id]
        L += [f"### Answer {r.answer_id} — {r.category} ({q.topic})",
              f"**Question:** {q.question}  ",
              f"**Reference:** {q.reference_answer}  ",
              f"**AI answer:** {ans.loc[r.answer_id, 'ai_answer']}", "",
              "| | Human | System |", "|---|---|---|",
              f"| Overall | {r.human_overall:.1f} | {r[sys_col]:.1f} |"]
        if hybrid_mode:
            missing = json.loads(r.missing_concepts) if isinstance(r.missing_concepts, str) else []
            L += [f"| Correctness | {r.human_correctness:.1f} | {r.correctness:.0f} |",
                  f"| Relevance | {r.human_relevance:.1f} | {r.relevance:.0f} |",
                  f"| Completeness | {r.human_completeness:.1f} | {r.completeness:.0f} |", "",
                  f"Semantic similarity {r.semantic_similarity:.2f} · concept coverage "
                  f"{int(r.concepts_covered)}/{int(r.concepts_total)} · LLM-only {r.llm_only_score:.1f} · "
                  f"keyword {r.keyword_score:.1f}  ",
                  f"Missing concepts: {', '.join(missing) if missing else 'none'}  "]
        else:
            L += [f"| (human correctness / relevance / completeness) | "
                  f"{r.human_correctness:.1f} / {r.human_relevance:.1f} / {r.human_completeness:.1f} | |", "",
                  f"Keyword score for comparison: {r.keyword_score:.1f}  "]
        L += [f"**Likely cause (auto, verify!):** {cause(r)}  ",
              "**Your explanation:** _write 1–2 sentences here_", ""]

    with open(f"{R}/error_analysis.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    big.assign(likely_cause=tags).to_csv(f"{R}/error_cases.csv", index=False)
    print("\n".join(L[:6]))
    print(f"\nWritten {R}/error_analysis.md and {R}/error_cases.csv")


if __name__ == "__main__":
    main()
