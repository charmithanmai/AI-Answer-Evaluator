"""Compare the 4 methods against human judgments. Produces every table and graph.

    python -m evaluation.comparison

Needs: data/human_scores.csv (from rating_sheets merge)
       results/system_scores.csv (from run_experiments)
Writes into results/:
    inter_rater.csv            how much the human raters agree with each other
    main_comparison.csv        THE results table (MAE, RMSE, Pearson, Spearman, Within ±1)
    per_category_mae.csv       which method fails on which kind of answer
    criterion_agreement.csv    hybrid's correctness/relevance/completeness vs humans'
    weight_tuning.csv          do different weights agree better with humans? (cross-validated)
    fig_*.png                  graphs for the report
    merged.csv                 everything in one table (used by error_analysis)
"""
import itertools

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from evaluation.metrics import (HUMAN_WEIGHTS, all_metrics, human_overall, mae,
                                pearson, weighted_kappa, within)

R = "results"
METHODS = {
    "Keyword": "keyword_score",
    "Semantic": "semantic_score",
    "LLM-only": "llm_only_score",
    "Hybrid (ours)": "overall_score",
}
COLORS = {"Keyword": "#9aa5b1", "Semantic": "#6c8ebf", "LLM-only": "#d79b00", "Hybrid (ours)": "#2e7d32"}
COMPONENTS = ["correctness", "relevance", "completeness", "semantic_similarity", "concept_coverage"]


def load():
    h = pd.read_csv("data/human_scores.csv")
    h["overall"] = h.apply(human_overall, axis=1)
    s = pd.read_csv(f"{R}/system_scores.csv")
    return h, s


def inter_rater(h):
    """Agreement between the two humans on each answer — the ceiling for any system."""
    rows = []
    for (r1, r2) in [("A", "C"), ("A", "B"), ("B", "C")]:
        p = h[h.rater == r1].merge(h[h.rater == r2], on="answer_id", suffixes=("_1", "_2"))
        for c in ["correctness", "relevance", "completeness", "overall"]:
            rows.append({"pair": f"{r1}-{r2}", "criterion": c, "n": len(p),
                         "MAE": mae(p[c + "_1"], p[c + "_2"]),
                         "Pearson": pearson(p[c + "_1"], p[c + "_2"]),
                         "Weighted kappa": weighted_kappa(p[c + "_1"], p[c + "_2"]),
                         "Within ±1 (%)": within(p[c + "_1"], p[c + "_2"])})
    # all pairs pooled
    first = h.sort_values("rater").groupby("answer_id").nth(0).set_index("answer_id")
    second = h.sort_values("rater").groupby("answer_id").nth(1).set_index("answer_id")
    for c in ["correctness", "relevance", "completeness", "overall"]:
        a, b = first[c], second.loc[first.index, c]
        rows.append({"pair": "ALL", "criterion": c, "n": len(a), "MAE": mae(a, b),
                     "Pearson": pearson(a, b), "Weighted kappa": weighted_kappa(a, b),
                     "Within ±1 (%)": within(a, b)})
    return pd.DataFrame(rows)


MIN_N = 10  # a method needs at least this many scored answers to be reported


def main():
    h, s = load()
    ir = inter_rater(h)
    ir.round(3).to_csv(f"{R}/inter_rater.csv", index=False)

    hm = h.groupby("answer_id")[["correctness", "relevance", "completeness", "overall"]].mean()
    hm = hm.add_prefix("human_").reset_index()
    df = s.merge(hm, on="answer_id")
    for c in list(METHODS.values()) + COMPONENTS:
        if c not in df:
            df[c] = np.nan
    df.to_csv(f"{R}/merged.csv", index=False)

    # each method is evaluated on the answers it actually scored
    counts = {m: int(df[c].notna().sum()) for m, c in METHODS.items()}
    avail = {m: c for m, c in METHODS.items() if counts[m] >= MIN_N}
    missing = [f"{m} ({counts[m]}/{len(df)})" for m in METHODS if m not in avail]
    if missing:
        print("NOTE: not enough scores yet for: " + ", ".join(missing)
              + ". They are left out; re-run run_experiments, then this script again.")

    # ---- 1. main table
    rows = {}
    for m, c in avail.items():
        d = df.dropna(subset=[c])
        rows[m] = {"n": len(d), **all_metrics(d.human_overall, d[c])}
    main_tab = pd.DataFrame(rows).T
    hc = ir[(ir.pair == "ALL") & (ir.criterion == "overall")].iloc[0]
    main_tab.loc["Human vs human (ceiling)"] = {"n": hc["n"], "MAE": hc["MAE"], "RMSE": np.nan,
                                                "Pearson": hc["Pearson"], "Spearman": np.nan,
                                                "Within ±1 (%)": hc["Within ±1 (%)"]}
    main_tab["n"] = main_tab["n"].astype(int)
    main_tab.index.name = "Method"
    main_tab.round(3).to_csv(f"{R}/main_comparison.csv")

    # ---- 2. per category
    cat = pd.DataFrame({m: df.dropna(subset=[c]).groupby("category")
                        .apply(lambda g, c=c: mae(g.human_overall, g[c]))
                        for m, c in avail.items()})
    cat["n"] = df.groupby("category").size()
    cat.round(2).to_csv(f"{R}/per_category_mae.csv")

    means = df.groupby("category")[["human_overall"] + list(avail.values())].mean()
    means.columns = ["Human"] + list(avail)
    means = means.sort_values("Human", ascending=False)
    means.round(2).to_csv(f"{R}/per_category_mean_score.csv")

    # ---- 3 + 4. hybrid-only analyses (need Gemini scores)
    crit = wt = None
    hyb = df.dropna(subset=COMPONENTS + ["overall_score"])
    if len(hyb) >= MIN_N:
        crit = pd.DataFrame({c: all_metrics(hyb[f"human_{c}"], hyb[c])
                             for c in ["correctness", "relevance", "completeness"]}).T
        crit.loc["completeness ~ concept_coverage x10"] = all_metrics(hyb.human_completeness,
                                                                    hyb.concept_coverage * 10)
        crit.round(3).to_csv(f"{R}/criterion_agreement.csv")
        if hyb.topic.nunique() >= 2:
            wt = tune_weights(hyb)
            wt.to_csv(f"{R}/weight_tuning.csv", index=False)

    # ---- 5. graphs
    plots(df, main_tab, cat, avail)

    pd.set_option("display.width", 160)
    print("\n=== INTER-RATER AGREEMENT (overall) ===")
    print(ir[ir.criterion == "overall"].round(3).to_string(index=False))
    print("\n=== MAIN COMPARISON vs HUMAN OVERALL ===")
    print(main_tab.round(3).to_string())
    print("\n=== MAE PER ANSWER CATEGORY ===")
    print(cat.round(2).to_string())
    print("\n=== MEAN SCORE PER CATEGORY (does each method rank answer types like humans?) ===")
    print(means.round(2).to_string())
    if crit is not None:
        print("\n=== HYBRID CRITERIA vs HUMAN CRITERIA ===")
        print(crit.round(3).to_string())
    if wt is not None:
        print("\n=== WEIGHT TUNING ===")
        print(wt.to_string(index=False))
    print(f"\nAll tables and figures saved in {R}/")


def _score(df, w):
    return (w[0] * df.correctness + w[1] * df.relevance + w[2] * df.completeness
            + w[3] * df.semantic_similarity * 10 + w[4] * df.concept_coverage * 10)


def _grid(step=0.1):
    vals = np.round(np.arange(0, 1 + 1e-9, step), 2)
    for w in itertools.product(vals, repeat=5):
        if abs(sum(w) - 1) < 1e-6:
            yield w


def tune_weights(df):
    """Leave-one-topic-out: pick best weights on 5 topics, test on the 6th.
    Reporting the held-out MAE keeps the claim honest (no tuning on test data)."""
    grid = list(_grid())
    initial = (0.4, 0.2, 0.2, 0.1, 0.1)
    rows, held_out_tuned, held_out_init = [], [], []
    for topic in df.topic.unique():
        train, test = df[df.topic != topic], df[df.topic == topic]
        best = min(grid, key=lambda w: mae(train.human_overall, _score(train, w)))
        held_out_tuned.append(np.abs(test.human_overall - _score(test, best)))
        held_out_init.append(np.abs(test.human_overall - _score(test, initial)))
    best_all = min(grid, key=lambda w: mae(df.human_overall, _score(df, w)))
    rows.append({"setting": "Initial weights (0.4/0.2/0.2/0.1/0.1)",
                 "weights": str(initial),
                 "held-out MAE": round(float(pd.concat(held_out_init).mean()), 3),
                 "Pearson (all)": round(pearson(df.human_overall, _score(df, initial)), 3)})
    rows.append({"setting": "Tuned weights (leave-one-topic-out)",
                 "weights": "chosen per fold",
                 "held-out MAE": round(float(pd.concat(held_out_tuned).mean()), 3),
                 "Pearson (all)": np.nan})
    rows.append({"setting": "Best weights on full data (for reporting only)",
                 "weights": str(tuple(float(x) for x in best_all)),
                 "held-out MAE": np.nan,
                 "Pearson (all)": round(pearson(df.human_overall, _score(df, best_all)), 3)})
    return pd.DataFrame(rows)


def plots(df, main_tab, cat, avail):
    names = list(avail)
    cols = [COLORS[n] for n in names]

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    t = main_tab.loc[names]
    ax[0].bar(names, t.MAE, color=cols); ax[0].set_title("Error vs human (lower is better)")
    ax[0].set_ylabel("MAE (points out of 10)")
    x = np.arange(len(names))
    ax[1].bar(x - 0.2, t.Pearson, 0.4, label="Pearson", color=cols)
    ax[1].bar(x + 0.2, t.Spearman, 0.4, label="Spearman", color=cols, alpha=0.55, hatch="//")
    ax[1].set_xticks(x); ax[1].set_xticklabels(names)
    ax[1].set_title("Correlation with human (higher is better)"); ax[1].set_ylim(min(0, t[["Pearson", "Spearman"]].min().min()), 1)
    ax[1].legend()
    for a in ax:
        a.tick_params(axis="x", labelrotation=15)
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(f"{R}/fig_main_comparison.png", dpi=200); plt.close(fig)

    fig, axes = plt.subplots(1, len(avail), figsize=(3.8 * len(avail), 3.8), sharey=True)
    axes = np.atleast_1d(axes)
    for a, (n, c) in zip(axes, avail.items()):
        a.scatter(df.human_overall, df[c], s=18, color=COLORS[n], alpha=0.75)
        a.plot([0, 10], [0, 10], "--", color="#888", lw=1)
        a.set_xlim(0, 10.3); a.set_ylim(0, 10.3); a.set_title(n)
        a.set_xlabel("Human overall")
        a.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("System score")
    fig.tight_layout(); fig.savefig(f"{R}/fig_scatter_vs_human.png", dpi=200); plt.close(fig)

    c2 = cat[names].sort_values(names[-1])
    fig, ax = plt.subplots(figsize=(10, 4.5))
    yy = np.arange(len(c2))
    for i, n in enumerate(names):
        w = 0.8 / len(names)
        ax.barh(yy + (i - (len(names) - 1) / 2) * w, c2[n], w, label=n, color=COLORS[n])
    ax.set_yticks(yy); ax.set_yticklabels(c2.index); ax.set_xlabel("MAE vs human")
    ax.set_title("Error by answer category"); ax.legend(loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(f"{R}/fig_per_category.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    main()
