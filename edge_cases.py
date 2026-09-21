from evaluator.semantic import semantic_similarity

REF = (
    "Deadlock occurs when processes wait indefinitely for resources held by "
    "each other. It requires mutual exclusion, hold and wait, no preemption, "
    "and circular wait."
)

REF_SHORT = "Deadlock is when processes wait on each other forever."

LONG_ANSWER = (
    "In an operating system, processes compete for limited resources such as "
    "files, memory and devices. Deadlock is the situation where a group of "
    "processes are each waiting for a resource that another process in the "
    "group is holding, so none of them can ever continue. For deadlock to "
    "happen, four conditions must hold together: mutual exclusion, hold and "
    "wait, no preemption, and circular wait. Operating systems handle it "
    "through prevention, avoidance, detection and recovery."
)

cases = [
    ("identical", REF, REF),
    ("paraphrase (correct)", REF,
     "Processes get stuck forever, each waiting for a resource another one holds."),
    ("incomplete (main idea only)", REF,
     "Deadlock occurs when two or more processes wait for resources held by one another, so none can proceed."),
    ("very short answer", REF, "Processes waiting."),
    ("relevant but WRONG", REF,
     "Deadlock is when a process uses all the CPU time so other processes finish early."),
    ("irrelevant", REF,
     "Photosynthesis is how plants convert sunlight into chemical energy."),
    ("short reference vs long correct answer", REF_SHORT, LONG_ANSWER),
    ("long reference vs short correct answer", LONG_ANSWER, REF_SHORT),
]

for name, ref, ans in cases:
    print(f"{semantic_similarity(ref, ans):.3f}   {name}")