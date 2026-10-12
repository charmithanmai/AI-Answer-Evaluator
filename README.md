# AI Answer Evaluator

A hybrid multi-criteria framework for evaluating AI-generated answers against
a reference answer. Instead of relying on a single method, it combines
semantic similarity, concept coverage, and rubric-based LLM evaluation into
one score with explainable feedback.

## The idea

Keyword matching misses paraphrased answers. Semantic similarity alone
can't tell a wrong-but-related answer from a correct one. LLM judging alone
has known reliability issues. This project combines all three and compares
the hybrid approach against each method individually, validated against
human evaluation.

## Example

**Question:** Explain deadlock in operating systems.

**Reference answer:** Deadlock occurs when processes wait indefinitely for
resources held by each other. It requires mutual exclusion, hold and wait,
no preemption, and circular wait.

**AI answer:** Deadlock occurs when two or more processes wait for resources
held by one another, so none can proceed.

**Output:**
```json
{
  "correctness": 8,
  "relevance": 9,
  "completeness": 6,
  "semantic_similarity": 0.931,
  "concept_coverage": 0.2,
  "overall_score": 7.33,
  "feedback": "Explains the main idea but omits some required conditions. Missing concepts: mutual exclusion, hold and wait, no preemption, circular wait."
}
```

## Project structure

evaluator/ - core evaluation engine (semantic similarity, concept
coverage, LLM judge, scoring, feedback)
baselines/ - keyword-only, semantic-only, and LLM-only baselines
backend/ - FastAPI server
frontend/ - web UI
data/ - question/answer dataset and human evaluation scores
evaluation/ - metrics (MAE, RMSE, Pearson, Spearman) and error analysis
tests/ - unit tests


## Tech stack

Python, FastAPI, Sentence Transformers, Gemini API, SQLite, HTML/CSS/JS

## Team

- CHARMI THANMAI M  — Evaluation engine (`evaluator/`)
- AISHWARYA VAIDYANATHAN — Dataset, baselines, experiments (`data/`, `evaluation/`)
- AYUSHI GUPTA — Backend + frontend (`backend/`, `frontend/`)

## Status

In development. Built over a 10-day sprint: engine, baselines, human
evaluation, and comparison metrics.