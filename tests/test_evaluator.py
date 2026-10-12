from evaluator import evaluate_answer
from evaluator.concepts import concept_coverage, extract_concepts
from evaluator.preprocessing import clean_text
from evaluator.semantic import semantic_similarity

REF = (
    "Deadlock occurs when processes wait indefinitely for resources held by "
    "each other. It requires mutual exclusion, hold and wait, no preemption, "
    "and circular wait."
)

EXPECTED_KEYS = {
    "correctness", "relevance", "completeness", "semantic_similarity",
    "concept_coverage", "concepts_covered", "concepts_total",
    "missing_concepts", "overall_score", "feedback",
}


# --- preprocessing ---

def test_clean_text_handles_none():
    assert clean_text(None) == ""


def test_clean_text_collapses_whitespace():
    assert clean_text("  hello \n\n  world\t ") == "hello world"


def test_clean_text_fixes_curly_quotes():
    assert clean_text("it\u2019s") == "it's"


# --- semantic similarity ---

def test_identical_text_scores_near_one():
    assert semantic_similarity(REF, REF) > 0.99


def test_similar_scores_higher_than_unrelated():
    similar = "Deadlock happens when processes are stuck waiting for each other's resources."
    unrelated = "Photosynthesis is how plants convert sunlight into chemical energy."
    assert semantic_similarity(REF, similar) > semantic_similarity(REF, unrelated)


def test_empty_input_returns_zero():
    assert semantic_similarity(REF, "") == 0.0
    assert semantic_similarity("", REF) == 0.0


def test_score_stays_between_0_and_1():
    score = semantic_similarity(REF, "x")
    assert 0.0 <= score <= 1.0


# --- the frozen JSON contract ---

def test_evaluate_answer_returns_all_keys():
    result = evaluate_answer("Explain deadlock.", REF, "Processes wait for each other.")
    assert EXPECTED_KEYS.issubset(result.keys())


def test_evaluate_answer_does_not_crash_on_empty_answer():
    result = evaluate_answer("Explain deadlock.", REF, "")
    assert EXPECTED_KEYS.issubset(result.keys())


# --- concept coverage ---

def test_extract_concepts_splits_the_list():
    concepts = extract_concepts(REF)
    assert len(concepts) == 5
    assert "no preemption" in concepts


def test_full_answer_covers_everything():
    assert concept_coverage(REF, REF)["coverage"] == 1.0


def test_irrelevant_answer_covers_nothing():
    result = concept_coverage(
        REF, "Photosynthesis is how plants convert sunlight into chemical energy."
    )
    assert result["covered"] == 0

from evaluator.llm_judge import llm_rubric_evaluate


# --- LLM judge ---

def test_llm_judge_returns_expected_keys():
    result = llm_rubric_evaluate(
        "Explain deadlock in operating systems.",
        REF,
        "Deadlock occurs when processes wait for each other's resources.",
    )
    assert {"correctness", "relevance", "completeness", "feedback"}.issubset(result.keys())


def test_llm_judge_scores_are_in_range():
    result = llm_rubric_evaluate(
        "Explain deadlock in operating systems.",
        REF,
        "Deadlock occurs when processes wait for each other's resources.",
    )
    for key in ("correctness", "relevance", "completeness"):
        assert 0 <= result[key] <= 10   