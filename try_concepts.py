from evaluator.concepts import extract_concepts

REFS = {
    "deadlock": (
        "Deadlock occurs when processes wait indefinitely for resources held by "
        "each other. It requires mutual exclusion, hold and wait, no preemption, "
        "and circular wait."
    ),
    "primary key": (
        "A primary key uniquely identifies each row in a table. "
        "It cannot contain NULL values. Each table can have only one primary key."
    ),
    "TCP": "TCP is connection-oriented, reliable, ordered, and error-checked.",
}

for name, ref in REFS.items():
    print(f"\n{name}")
    for i, concept in enumerate(extract_concepts(ref), 1):
        print(f"  {i} -> {concept}")