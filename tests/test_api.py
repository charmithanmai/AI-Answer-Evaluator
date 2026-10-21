import pytest
from fastapi.testclient import TestClient

import backend.api.evaluate as evaluate_module
import backend.database as database
from backend.main import app

client = TestClient(app)

VALID = {
    "question": "Explain deadlock in operating systems.",
    "reference_answer": "Deadlock occurs when processes wait indefinitely for resources held by each other.",
    "ai_answer": "Deadlock occurs when two or more processes wait for resources held by one another.",
}

RESULT_FIELDS = [
    "correctness",
    "relevance",
    "completeness",
    "semantic_similarity",
    "concept_coverage",
    "overall_score",
    "feedback",
]


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    """Every test gets its own empty database, so your real history.db is never touched."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test_history.db")
    database.init_db()


@pytest.fixture
def mock_mode(monkeypatch):
    """Use the mock evaluator, so no LLM call is made."""
    monkeypatch.setattr(evaluate_module, "USE_MOCK", True)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.parametrize("field", ["question", "reference_answer", "ai_answer"])
@pytest.mark.parametrize("bad_value", ["", "   "])
def test_empty_field_is_rejected(field, bad_value):
    body = {**VALID, field: bad_value}
    response = client.post("/evaluate", json=body)
    assert response.status_code == 422


def test_missing_field_is_rejected():
    body = {"question": VALID["question"], "reference_answer": VALID["reference_answer"]}
    response = client.post("/evaluate", json=body)
    assert response.status_code == 422


def test_evaluate_returns_all_fields(mock_mode):
    response = client.post("/evaluate", json=VALID)
    assert response.status_code == 200
    data = response.json()
    for field in RESULT_FIELDS:
        assert field in data


def test_scores_are_in_range(mock_mode):
    data = client.post("/evaluate", json=VALID).json()
    for field in ["correctness", "relevance", "completeness", "overall_score"]:
        assert 0 <= data[field] <= 10
    assert 0 <= data["semantic_similarity"] <= 1
    assert 0 <= data["concept_coverage"] <= 1


def test_history_starts_empty():
    assert client.get("/history").json() == []


def test_evaluation_is_saved_to_history(mock_mode):
    client.post("/evaluate", json=VALID)
    history = client.get("/history").json()
    assert len(history) == 1
    assert history[0]["question"] == VALID["question"]
    assert "created_at" in history[0]


def test_history_is_newest_first(mock_mode):
    client.post("/evaluate", json={**VALID, "question": "First question"})
    client.post("/evaluate", json={**VALID, "question": "Second question"})
    history = client.get("/history").json()
    assert history[0]["question"] == "Second question"


def test_history_limit(mock_mode):
    for number in range(3):
        client.post("/evaluate", json={**VALID, "question": "Question " + str(number)})
    assert len(client.get("/history?limit=2").json()) == 2


def test_clear_history(mock_mode):
    client.post("/evaluate", json=VALID)
    response = client.delete("/history")
    assert response.status_code == 200
    assert response.json()["deleted"] == 1
    assert client.get("/history").json() == []


def test_html_in_answer_is_stored_as_text(mock_mode):
    tricky = '<script>alert("x")</script>'
    client.post("/evaluate", json={**VALID, "ai_answer": tricky})
    assert client.get("/history").json()[0]["ai_answer"] == tricky


def test_failed_evaluation_is_not_saved(monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("LLM down")

    monkeypatch.setattr(evaluate_module, "USE_MOCK", False)
    monkeypatch.setattr(evaluate_module, "real_evaluation", broken)

    response = client.post("/evaluate", json=VALID)
    assert response.status_code == 500
    assert "Evaluation failed" in response.json()["detail"]
    assert client.get("/history").json() == []
