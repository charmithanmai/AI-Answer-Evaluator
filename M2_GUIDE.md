# Member 2 — Data + Baselines + Experiments: step-by-step

All commands run from the **repo root** (the folder that contains `evaluator/`).
Every script is resumable — if something crashes or Gemini hits a quota, just run the same command again.

---

## STEP 0 — Setup (once, ~15 min)

1. Get Member 1's repo and add these files into it:
   ```
   git clone https://github.com/charmithanmai/AI-Answer-Evaluator
   cd AI-Answer-Evaluator
   git checkout -b member2-experiments
   ```
   Copy in from the zip: `baselines/`, `data/`, `evaluation/`, `results/`, `M2_GUIDE.md`.

2. Create a virtual environment and install **the same packages Member 1 uses** (do not install anything else):
   ```
   python -m venv venv
   venv\Scripts\activate          # Windows
   source venv/bin/activate       # Mac/Linux
   pip install -r requirements.txt
   pip install matplotlib
   ```
   `matplotlib` is the only extra library (for graphs). torch is big — the install can take 5–10 min.

3. Create a file named `.env` in the repo root (ask Member 1 for the key, or make your own free one at Google AI Studio):
   ```
   GEMINI_API_KEY=your_key_here
   ```
   `.env` is already in `.gitignore` — **never commit it**.

4. Check everything works:
   ```
   python -m baselines.keyword               # should print a score
   python -m baselines.semantic_baseline     # first run downloads the model (~90 MB)
   python run_demo.py                        # Member 1's demo — confirms Gemini works
   ```

---

## STEP 1 — Dataset (Day 2–4 work)

**Already have your own questions?** Put them in `data/questions.csv` with columns
`question_id, topic, question, reference_answer`. Otherwise use the 30 provided (6 topics × 5).

Reference-answer tip: Member 1's concept extractor splits on sentences and on lists with 2+ commas.
Write one fact per sentence or as a comma list, and avoid "e.g." and "X, also known as Y," patterns.

Generate the 90 answers (30 questions × 3 categories, each of the 10 categories appears 9 times, ~10 min):
```
python -m data.generate_answers
```
→ `data/answers.csv` (`answer_id, question_id, category, ai_answer`)

**⚠ Must do: open `data/answers.csv` and read all 90.** If a "hallucinated" answer has no false fact,
or a "very_short" one is long, fix the text by hand. Wrong labels ruin the category analysis.

Commit: `git add data && git commit -m "Add dataset: 30 questions, 90 answers"`

---

## STEP 2 — Human evaluation (Day 7–8, the slow part — start TODAY)

```
python -m evaluation.rating_sheets make
```
→ `data/rating_sheets/rater_A.csv`, `rater_B.csv`, `rater_C.csv`, `RATING_GUIDE.txt`

- A = answers 1–60, B = 31–90, C = 1–30 & 61–90 → every answer gets exactly 2 raters (as in the plan).
- Sheets are blind (no category) and shuffled.
- Send each person their sheet + `RATING_GUIDE.txt`. They fill `correctness`, `relevance`,
  `completeness` (whole numbers 0–10) in Excel/Google Sheets, then **save as CSV with the same name**.
- Rule: rate alone, no discussion, and **before** anyone sees the system's scores.
- ~60 answers × ~1 min = about an hour per person.

When all three sheets are back in `data/rating_sheets/`:
```
python -m evaluation.rating_sheets merge
```
→ `data/human_scores.csv`. If it prints "FIX THESE FIRST", fix the listed cells and run again.

---

## STEP 3 — Run all 4 evaluators (can run WHILE humans are rating)

Quick test first (no API):
```
python -m evaluation.run_experiments --offline --limit 3
```
Then the real run (2 Gemini calls per answer, about 20 min at Member 1's rate limit):
```
python -m evaluation.run_experiments
```
→ `results/system_scores.csv` with keyword, semantic, LLM-only and hybrid scores.
If it says "N answers still incomplete" (Gemini errors / 503 overloaded), run it again — only the missing ones are redone.
Gemini failures are left blank, NOT scored 0, so they don't poison the results.

---

## STEP 4 — Metrics + comparison (Day 8–9)

```
python -m evaluation.comparison
```
Prints and saves to `results/`:

| File | What it is | Goes in report as |
|---|---|---|
| `inter_rater.csv` | Agreement between the 2 humans (MAE, Pearson, weighted kappa, within ±1) | "Human agreement / ceiling" |
| `main_comparison.csv` | **THE table**: MAE, RMSE, Pearson, Spearman, Within ±1 for all 4 methods + human ceiling | Main results table |
| `per_category_mae.csv` | Error of each method per answer type | "Where each method fails" |
| `per_category_mean_score.csv` | Average score each method gives each category | Shows semantic/keyword over-scoring wrong answers |
| `criterion_agreement.csv` | Hybrid's correctness/relevance/completeness vs human's | Component analysis |
| `weight_tuning.csv` | Initial weights vs tuned (leave-one-topic-out, held-out MAE) | "Does tuning help?" (Objective in plan §7) |
| `fig_main_comparison.png`, `fig_scatter_vs_human.png`, `fig_per_category.png` | Graphs | Figures |

Then tune Member 1's concept threshold (no API calls):
```
python -m evaluation.tune_threshold
```
→ `results/threshold_tuning.csv`. Send the best value to Member 1 (her notes.md asks for exactly this).

---

## STEP 5 — Error analysis (Day 9)

```
python -m evaluation.error_analysis
```
→ `results/error_analysis.md` — the 15 biggest disagreements with all component scores and an
**automatic guess** of the cause. Read each case, correct the guess, and fill in "Your explanation".
Pick 3–5 clear examples for the report (the plan §13 lists the kinds to look for).

---

## STEP 6 — Final results (Day 10)

1. Commit and push:
   ```
   git add baselines data evaluation results M2_GUIDE.md
   git commit -m "Member 2: baselines, human evaluation, metrics, comparison, error analysis"
   git push -u origin member2-experiments
   ```
   Then open a pull request to Member 1's repo (or ask her to add you as collaborator).
2. Write the results section in this order: dataset → human agreement → main table → per-category →
   weight/threshold tuning → error analysis → limitations.

### How to read the results honestly
- **Human ceiling:** no system can be expected to beat the human-vs-human agreement.
- If hybrid isn't best on everything, say so — the plan explicitly says we do NOT claim it's universally better.
  "Hybrid has lower error on hallucinated/relevant-but-incorrect answers but not on very short answers" is a good finding.
- Only quote **held-out** MAE for tuned weights; the "best on full data" row is optimistic.
- 90 answers is small: mention that differences of ~0.1–0.2 MAE may not be meaningful.
