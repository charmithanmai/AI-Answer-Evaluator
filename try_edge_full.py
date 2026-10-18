from evaluator import evaluate_answer

Q = "Explain deadlock in operating systems."
REF = (
    "Deadlock occurs when processes wait indefinitely for resources held by "
    "each other. It requires mutual exclusion, hold and wait, no preemption, "
    "and circular wait."
)

CASES = {
    "full correct": REF,
    "paraphrase (correct)":
        "Processes get stuck forever, each waiting for a resource another one holds.",
    "incomplete (main idea only)":
        "Deadlock occurs when two or more processes wait for resources held by one another, so none can proceed.",
    "relevant but WRONG":
        "Deadlock is when a process uses all the CPU time so other processes finish early.",
    "very short": "Processes waiting.",
    "irrelevant":
        "Photosynthesis is how plants convert sunlight into chemical energy.",
    "empty answer": "",
}

for name, answer in CASES.items():
    r = evaluate_answer(Q, REF, answer)
    print(f"\n{name}")
    print(f"  overall {r['overall_score']} | correctness {r['correctness']}  relevance {r['relevance']}  completeness {r['completeness']}")
    print(f"  similarity {r['semantic_similarity']} | coverage {r['concept_coverage']}")
    print(f"  feedback: {r['feedback']}")