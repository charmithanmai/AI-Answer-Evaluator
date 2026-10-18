import csv
import sys

import pandas as pd

from evaluator import evaluate_answer

FIELDS = [
    "correctness", "relevance", "completeness", "semantic_similarity",
    "concept_coverage", "concepts_covered", "concepts_total",
    "missing_concepts", "overall_score", "feedback",
]


def main(input_path, output_path):
    df = pd.read_csv(input_path).fillna("")
    needed = {"question", "reference_answer", "ai_answer"}
    absent = needed - set(df.columns)
    if absent:
        raise SystemExit(f"Input CSV is missing columns: {sorted(absent)}")

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(df.columns) + FIELDS)
        writer.writeheader()
        for i, row in df.iterrows():
            result = evaluate_answer(row["question"], row["reference_answer"], row["ai_answer"])
            result["missing_concepts"] = "; ".join(result["missing_concepts"])
            out = row.to_dict()
            out.update(result)
            writer.writerow(out)
            f.flush()  # saved after every row, so a crash doesn't lose the work
            print(f"{i + 1}/{len(df)} done, overall {result['overall_score']}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python run_batch.py input.csv output.csv")
    main(sys.argv[1], sys.argv[2])