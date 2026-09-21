import json
from evaluator import evaluate_answer

result = evaluate_answer(
    question="Explain deadlock in operating systems.",
    reference_answer=(
        "Deadlock occurs when processes wait indefinitely for resources held by each "
        "other. It requires mutual exclusion, hold and wait, no preemption, and circular wait."
    ),
    ai_answer=(
        "Deadlock occurs when two or more processes wait for resources held by one "
        "another, so none can proceed."
    ),
)
print(json.dumps(result, indent=2))