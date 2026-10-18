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

from evaluator.scoring import aggregate, WEIGHTS


# --- score aggregation ---

def test_weights_add_up_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_perfect_scores_give_ten():
    assert aggregate(10, 10, 10, 1.0, 1.0) == 10.0


def test_zero_scores_give_zero():
    assert aggregate(0, 0, 0, 0.0, 0.0) == 0.0


def test_stub_example_matches_hand_calculation():
    assert aggregate(8, 9, 6, 0.86, 0.75) == 7.81


from evaluator.llm_judge import _clean_score


# --- LLM score cleaning ---

def test_clean_score_clamps_high_values():
    assert _clean_score(11) == 10.0


def test_clean_score_clamps_negative_values():
    assert _clean_score(-3) == 0.0


def test_clean_score_accepts_numbers_as_text():
    assert _clean_score("8") == 8.0

from evaluator.feedback import build_feedback


# --- feedback ---

def test_feedback_lists_missing_concepts():
    text = build_feedback("Good start.", ["no preemption", "circular wait"], 7.5)
    assert "no preemption" in text and "circular wait" in text


def test_feedback_includes_band_and_score():
    text = build_feedback("Nice.", [], 9.0)
    assert "Excellent" in text and "9.0/10" in text


def test_feedback_handles_llm_failure():
    text = build_feedback("LLM evaluation failed after 3 attempts: 503", ["circular wait"], 1.1)
    assert "unavailable" in text
    assert "Weak" not in text
    assert "circular wait" in text


def test_feedback_handles_empty_inputs():
    assert build_feedback("", [], None) == ""
    assert build_feedback(None, None) == ""

# --- edge cases ---

def test_concept_coverage_with_empty_reference():
    result = concept_coverage("", "Some answer.")
    assert result["total"] == 0
    assert result["coverage"] == 0.0


def test_concept_coverage_with_empty_answer():
    result = concept_coverage(REF, "")
    assert result["covered"] == 0
    assert result["total"] == 5