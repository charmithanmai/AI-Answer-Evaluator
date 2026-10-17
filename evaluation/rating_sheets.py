"""Human evaluation: make blind rating sheets, then merge them back.

STEP A — make the sheets (one per team member):
    python -m evaluation.rating_sheets make

  Assignment from the project plan (every answer gets exactly 2 raters):
      A -> answers 1-60     B -> answers 31-90     C -> answers 1-30 and 61-90
  Sheets are BLIND (no category, no system scores) and SHUFFLED, so raters
  are not biased by knowing "this one is supposed to be hallucinated".

STEP B — each person fills correctness / relevance / completeness (0-10)
  in their sheet (Excel or Google Sheets, then save/download as CSV with the
  same file name). Rate ALONE. Do not discuss scores until all are done.

STEP C — merge:
    python -m evaluation.rating_sheets merge
  -> data/human_scores.csv  (one row per answer per rater)
"""
import os
import sys

import pandas as pd

SHEET_DIR = "data/rating_sheets"
ASSIGN = {
    "A": list(range(1, 61)),
    "B": list(range(31, 91)),
    "C": list(range(1, 31)) + list(range(61, 91)),
}
CRITERIA = ["correctness", "relevance", "completeness"]

GUIDE = """HUMAN RATING GUIDE (everyone uses the same rules)

Score each answer 0-10 on three criteria. Compare it with the reference answer.

CORRECTNESS - are the statements in the answer true?
  10 = everything stated is accurate      5 = mix of right and wrong
   0 = the main claim is wrong
  (A short answer can still be 10 here if what it says is right.)

RELEVANCE - does it answer THIS question?
  10 = directly on the question           5 = partly on topic / drifts
   0 = about something else

COMPLETENESS - does it cover the points in the reference?
  10 = all reference points               5 = about half
   0 = none of them
  (Extra correct detail is fine. Count missing points, not length.)

Rules:
- Rate alone. Do not look at other people's sheets.
- Do not change a score after seeing the system's output.
- Whole numbers only. Leave a note in the 'notes' column if unsure.
"""


def make():
    answers = pd.read_csv("data/answers.csv")
    qs = pd.read_csv("data/questions.csv")
    df = answers.merge(qs[["question_id", "question", "reference_answer"]], on="question_id")
    os.makedirs(SHEET_DIR, exist_ok=True)
    for rater, ids in ASSIGN.items():
        sheet = df[df.answer_id.isin(ids)][["answer_id", "question", "reference_answer", "ai_answer"]]
        sheet = sheet.sample(frac=1, random_state=ord(rater)).reset_index(drop=True)
        for c in CRITERIA:
            sheet[c] = ""
        sheet["notes"] = ""
        path = f"{SHEET_DIR}/rater_{rater}.csv"
        sheet.to_csv(path, index=False)
        print(f"{path}: {len(sheet)} answers")
    with open(f"{SHEET_DIR}/RATING_GUIDE.txt", "w") as f:
        f.write(GUIDE)
    print(f"{SHEET_DIR}/RATING_GUIDE.txt written — send it with each sheet.")


def merge():
    frames, problems = [], []
    for rater, ids in ASSIGN.items():
        path = f"{SHEET_DIR}/rater_{rater}.csv"
        if not os.path.exists(path):
            problems.append(f"missing {path}")
            continue
        s = pd.read_csv(path)
        for c in CRITERIA:
            s[c] = pd.to_numeric(s[c], errors="coerce")
            bad = s[s[c].isna() | (s[c] < 0) | (s[c] > 10)]
            for aid in bad.answer_id:
                problems.append(f"rater {rater}, answer {aid}: '{c}' empty or not 0-10")
        missing_ids = set(ids) - set(s.answer_id)
        if missing_ids:
            problems.append(f"rater {rater}: answers missing from sheet {sorted(missing_ids)}")
        s["rater"] = rater
        frames.append(s[["answer_id", "rater"] + CRITERIA])

    if problems:
        print("FIX THESE FIRST:\n  " + "\n  ".join(problems))
        sys.exit(1)

    out = pd.concat(frames).sort_values(["answer_id", "rater"])
    counts = out.groupby("answer_id").size()
    assert (counts == 2).all(), f"answers without exactly 2 ratings: {counts[counts != 2].index.tolist()}"
    out.to_csv("data/human_scores.csv", index=False)
    print(f"data/human_scores.csv: {len(out)} ratings, {out.answer_id.nunique()} answers, 2 raters each")


if __name__ == "__main__":
    {"make": make, "merge": merge}[sys.argv[1] if len(sys.argv) > 1 else "make"]()
