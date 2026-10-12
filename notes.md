# M1 Notes for the Report

## Finding 1: Semantic similarity alone is not enough
Test file: edge_cases.py (contains all the test sentences)
Model: all-MiniLM-L6-v2, cosine similarity

Results:
1.000  identical
0.608  paraphrase (correct)
0.931  incomplete (main idea only)
0.510  very short answer
0.909  relevant but WRONG
0.049  irrelevant
0.818  short reference vs long correct answer
0.818  long reference vs short correct answer

What it shows:
- A relevant but WRONG answer (0.909) scored higher than a correct
  paraphrase (0.608). Embeddings measure topic closeness, not truth.
- The incomplete answer scored 0.931 even though it misses all four
  necessary conditions.
- Cosine similarity is symmetric, so short-vs-long gives the same score
  in both directions. It cannot detect missing content.
- This motivates adding concept coverage and an LLM judge.

## Finding 2: Concept coverage catches what similarity misses
Test file: try_coverage.py
Method: extract concepts from the reference, then check each one with a
word match first, then a meaning match (threshold 0.55).

Results (5 concepts in the deadlock reference):
full correct:                5/5 (100%)
incomplete (main idea only): 1/5 (20%)   <- similarity gave 0.931
paraphrase (correct):        2/5 (40%)
relevant but WRONG:          1/5 (20%)
irrelevant:                  0/5 (0%)

Meaning-match scores seen: hits 0.73 to 0.98, closest miss 0.48.

What it shows:
- The incomplete answer drops from 0.931 similarity to 20% coverage.
  That gap is the reason this module exists.
- Wrong-but-relevant answer still got credit for the definition (0.84).
  Concept coverage measures topic touched, not truth. The LLM judge
  must catch factual errors.
- The paraphrase got "hold and wait" through the word check even though
  the words were scattered. The word check ignores order and proximity.

## Finding 3: LLM judge agrees with concept coverage independently
Question: Explain deadlock in operating systems.
Model: gemini-3.8-flash
Answer tested: "Deadlock occurs when two or more processes wait for
resources held by one another, so none can proceed." (incomplete answer)

LLM judge output:
correctness: 10, relevance: 10, completeness: 5
feedback: "Your definition is accurate, but you omitted the four
necessary conditions for deadlock to occur (mutual exclusion, hold
and wait, no preemption, and circular wait)."

Concept coverage (same answer): 1/5 (20%) — same four conditions
flagged as missing, found completely independently via embedding
similarity rather than an LLM call.

Two different methods agreeing on the same gap is evidence the
multi-criteria approach adds real signal beyond a single method.

## Known limitations (for the report)
- Concept extraction is rule-based. It can wrongly bundle the sentence
  subject with the first list item (example: "TCP is connection-oriented").
- A sentence like "Deadlock, also known as X, occurs when..." has two
  commas and would be wrongly split into a list.
- Abbreviations like "e.g." can confuse the sentence splitter.
- The embedding model truncates very long texts.
- The 0.55 threshold is a first guess based on 5 test cases only. Tune it
  against the human-scored dataset from M2 (Day 8).
- The initial score weights (0.40/0.20/0.20/0.10/0.10) are also untuned.
- LLM API reliability: observed a live 503 "model overloaded" error from
  Gemini during testing. Built in automatic retry (3 attempts,
  exponential backoff) with a safe zero-score fallback instead of
  crashing. This matches the reliability concerns noted in the
  LLM-as-a-judge literature (ACL Anthology) cited in the project plan.
- Model availability: gemini-2.5-flash was deprecated for new users
  mid-project; switched to gemini-3.8-flash. Model name is kept as a
  single constant (MODEL_NAME) in llm_judge.py so future renames are a
  one-line change.