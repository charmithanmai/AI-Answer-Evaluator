"""Error analysis: where does the hybrid system disagree with humans, and why?

    python -m evaluation.error_analysis

Needs results/merged.csv (run comparison.py first).
Writes results/error_analysis.md — a ready-to-edit draft for the report.
The 'likely cause' tags are automatic GUESSES from the component scores.
Read each case yourself and correct the tag before putting it in the report.
"""
import json

import pandas as pd

R = "results"
BIG = 2.0  # a disagreement of 2+ points (out of 10) counts as an error case


def likely_cause(r) -> str:
    over = r.overall_score > r.human_overall
    causes = []
    if over:
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


def main():
    df = pd.read_csv(f"{R}/merged.csv")
    df["error"] = df.overall_score - df.human_overall
    df["abs_error"] = df.error.abs()
    qs = pd.read_csv("data/questions.csv").set_index("question_id")
    ans = pd.read_csv("data/answers.csv").set_index("answer_id")

    big = df[df.abs_error >= BIG].sort_values("abs_error", ascending=False)
    over, under = big[big.error > 0], big[big.error < 0]

    # head-to-head: when does the hybrid beat / lose to LLM-only?
    df["hyb_err"] = df.abs_error
    df["llm_err"] = (df.llm_only_score - df.human_overall).abs()
    df["sem_err"] = (df.semantic_score - df.human_overall).abs()
    hyb_better_llm = (df.hyb_err < df.llm_err - 0.5).sum()
    llm_better_hyb = (df.llm_err < df.hyb_err - 0.5).sum()

    L = ["# Error Analysis — Hybrid evaluator vs human judgments", ""]
    L += [f"- Answers analysed: **{len(df)}**",
          f"- Large disagreements (|system − human| ≥ {BIG}): **{len(big)}** "
          f"({len(over)} over-scored, {len(under)} under-scored)",
          f"- Hybrid closer to humans than LLM-only (by >0.5 pt): **{hyb_better_llm}** answers; "
          f"LLM-only closer: **{llm_better_hyb}** answers",
          ""]

    L += ["## Error by category (mean signed error: + means system too generous)", "",
          "| Category | n | Mean error | Mean |error| |", "|---|---|---|---|"]
    for c, g in df.groupby("category"):
        L.append(f"| {c} | {len(g)} | {g.error.mean():+.2f} | {g.abs_error.mean():.2f} |")
    L.append("")

    tags = big.apply(likely_cause, axis=1)
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
        missing = json.loads(r.missing_concepts) if isinstance(r.missing_concepts, str) else []
        L += [f"### Answer {r.answer_id} — {r.category} ({q.topic})",
              f"**Question:** {q.question}  ",
              f"**Reference:** {q.reference_answer}  ",
              f"**AI answer:** {ans.loc[r.answer_id, 'ai_answer']}", "",
              f"| | Human | System |", "|---|---|---|",
              f"| Overall | {r.human_overall:.1f} | {r.overall_score:.1f} |",
              f"| Correctness | {r.human_correctness:.1f} | {r.correctness:.0f} |",
              f"| Relevance | {r.human_relevance:.1f} | {r.relevance:.0f} |",
              f"| Completeness | {r.human_completeness:.1f} | {r.completeness:.0f} |", "",
              f"Semantic similarity {r.semantic_similarity:.2f} · concept coverage "
              f"{int(r.concepts_covered)}/{int(r.concepts_total)} · LLM-only {r.llm_only_score:.1f} · "
              f"keyword {r.keyword_score:.1f}  ",
              f"Missing concepts: {', '.join(missing) if missing else 'none'}  ",
              f"**Likely cause (auto, verify!):** {likely_cause(r)}  ",
              "**Your explanation:** _write 1–2 sentences here_", ""]

    with open(f"{R}/error_analysis.md", "w") as f:
        f.write("\n".join(L))
    big.assign(likely_cause=tags).to_csv(f"{R}/error_cases.csv", index=False)
    print("\n".join(L[:8]))
    print(f"\nWritten {R}/error_analysis.md and {R}/error_cases.csv")


if __name__ == "__main__":
    main()
