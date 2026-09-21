from evaluator.concepts import concept_coverage

REF = (
    "Deadlock occurs when processes wait indefinitely for resources held by "
    "each other. It requires mutual exclusion, hold and wait, no preemption, "
    "and circular wait."
)

CASES = {
    "full correct": REF,
    "incomplete (main idea only)":
        "Deadlock occurs when two or more processes wait for resources held by one another, so none can proceed.",
    "paraphrase (correct)":
        "Processes get stuck forever, each waiting for a resource another one holds.",
    "relevant but WRONG":
        "Deadlock is when a process uses all the CPU time so other processes finish early.",
    "irrelevant":
        "Photosynthesis is how plants convert sunlight into chemical energy.",
}

for name, answer in CASES.items():
    result = concept_coverage(REF, answer)
    print(f"\n{name}: {result['covered']}/{result['total']} ({result['coverage']:.0%})")
    for d in result["details"]:
        mark = "YES" if d["covered"] else "no "
        print(f"   {mark}  {d['method']:<8} {d['score']:.2f}  {d['concept'][:55]}")