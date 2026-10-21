import json
import sqlite3
from datetime import datetime
from pathlib import Path

# The database file is created next to this file the first time the server starts
DB_PATH = Path(__file__).resolve().parent / "history.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                reference_answer TEXT NOT NULL,
                ai_answer TEXT NOT NULL,
                correctness REAL,
                relevance REAL,
                completeness REAL,
                semantic_similarity REAL,
                concept_coverage REAL,
                concepts_covered INTEGER,
                concepts_total INTEGER,
                missing_concepts TEXT,
                overall_score REAL,
                feedback TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def save_evaluation(question: str, reference_answer: str, ai_answer: str, result: dict) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO evaluations (
                question, reference_answer, ai_answer,
                correctness, relevance, completeness,
                semantic_similarity, concept_coverage,
                concepts_covered, concepts_total, missing_concepts,
                overall_score, feedback, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question,
                reference_answer,
                ai_answer,
                result["correctness"],
                result["relevance"],
                result["completeness"],
                result["semantic_similarity"],
                result["concept_coverage"],
                result.get("concepts_covered"),
                result.get("concepts_total"),
                json.dumps(result.get("missing_concepts", [])),
                result["overall_score"],
                result["feedback"],
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return cursor.lastrowid


def get_history(limit: int = 50) -> list:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM evaluations ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    history = []
    for row in rows:
        item = dict(row)
        item["missing_concepts"] = json.loads(item["missing_concepts"] or "[]")
        history.append(item)
    return history