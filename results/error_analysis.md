# Error Analysis — Semantic-only baseline vs human judgments

- Answers analysed: **90**
- Large disagreements (|system − human| ≥ 2.0): **33** (30 over-scored, 3 under-scored)
- Semantic closer to humans than keyword (by >0.5 pt): **45** answers; keyword closer: **31** answers

## Error by category (mean signed error: + means system too generous)

| Category | n | Human mean | System mean | Mean error | Mean |error| |
|---|---|---|---|---|---|
| correct_incomplete | 9 | 5.99 | 8.00 | +2.02 | 2.14 |
| fully_correct | 9 | 10.00 | 9.52 | -0.48 | 0.48 |
| hallucinated | 9 | 7.13 | 9.07 | +1.93 | 1.93 |
| irrelevant | 9 | 0.01 | 2.05 | +2.04 | 2.04 |
| mostly_correct | 9 | 8.47 | 9.16 | +0.69 | 1.04 |
| overly_verbose | 9 | 9.82 | 8.74 | -1.08 | 1.08 |
| paraphrased_correct | 9 | 9.87 | 8.18 | -1.69 | 1.69 |
| partially_correct | 9 | 5.87 | 8.21 | +2.35 | 2.35 |
| relevant_incorrect | 9 | 1.29 | 8.99 | +7.70 | 7.70 |
| very_short | 9 | 5.86 | 6.10 | +0.24 | 0.66 |

## Most frequent likely causes

- embedding measures topic overlap, not truth: wrong facts on the right topic score high: 13
- missing content is not detected: a partial answer is still 'similar' to the reference: 9
- off-topic answer from the same subject area shares vocabulary with the reference: 6
- unclear — inspect manually: 3
- correct answer with different wording gets lower similarity: 2

## Individual cases

### Answer 5 — relevant_incorrect (Operating Systems)
**Question:** What is the difference between a process and a thread?  
**Reference:** A process is an independent program in execution with its own address space. A thread is a lightweight unit of execution inside a process. Threads of the same process share memory, open files, and code. Creating and switching threads is cheaper than creating and switching processes.  
**AI answer:** A thread is a separate program with its own private memory, while a process is a part of a thread. Threads cannot share data with each other, and creating a thread is more expensive than creating a process.

| | Human | System |
|---|---|---|
| Overall | 0.1 | 8.7 |
| (human correctness / relevance / completeness) | 0.0 / 0.5 / 0.0 | |

Keyword score for comparison: 4.8  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** The answer reverses the process/thread relationship and makes false claims about memory sharing and creation cost, so humans scored it near 0. It reuses the reference's key words (thread, process, memory, creating), so the embedding sees it as very similar (8.7). Semantic similarity rewards the right topic and vocabulary, not correct facts.

### Answer 15 — relevant_incorrect (Operating Systems)
**Question:** Explain the Round Robin CPU scheduling algorithm.  
**Reference:** Round Robin gives each ready process a fixed time quantum in circular order. If a process does not finish within its quantum it is preempted and moved to the back of the ready queue. It is fair and gives good response time. A very small quantum causes high context switching overhead.  
**AI answer:** Round Robin always runs the shortest job first and lets each process run until it completes without interruption. Processes are never preempted, so a very small time quantum has no effect on overhead.

| | Human | System |
|---|---|---|
| Overall | 0.1 | 8.6 |
| (human correctness / relevance / completeness) | 0.0 / 0.5 / 0.0 | |

Keyword score for comparison: 3.5  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** This describes non-preemptive shortest-job-first, which is the opposite of Round Robin, yet it scores 8.6 because it talks about processes, time quantum and preemption just like the reference. Negating key facts ("never preempted") barely changes the sentence embedding, so the baseline cannot detect contradictions.

### Answer 45 — relevant_incorrect (DBMS)
**Question:** What is the difference between DELETE and TRUNCATE in SQL?  
**Reference:** DELETE removes selected rows using a WHERE clause and can be rolled back. TRUNCATE removes all rows from a table at once. TRUNCATE is faster because it does not log individual row deletions. DELETE fires triggers while TRUNCATE does not.  
**AI answer:** DELETE removes the entire table structure permanently and cannot be rolled back, while TRUNCATE removes only selected rows using a WHERE clause. TRUNCATE is slower because it logs every row, and it fires triggers for each deleted row.

| | Human | System |
|---|---|---|
| Overall | 1.0 | 9.3 |
| (human correctness / relevance / completeness) | 0.0 / 5.0 / 0.0 | |

Keyword score for comparison: 6.7  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** DELETE and TRUNCATE are swapped and the claims about rollback, logging and triggers are reversed. Because the answer contains almost every term from the reference, semantic similarity is 9.3, higher than some fully correct answers. Swapping which term each fact belongs to is invisible to whole-sentence embeddings.

### Answer 65 — relevant_incorrect (Programming)
**Question:** What is the difference between an array and a linked list?  
**Reference:** An array stores elements in contiguous memory and allows constant-time access by index. A linked list stores nodes that point to the next node. Linked lists allow cheap insertion and deletion but need linear time to access an element. Arrays have a fixed size while linked lists grow dynamically.  
**AI answer:** A linked list stores elements in contiguous memory and allows constant-time access by index, while an array stores scattered nodes with pointers. Arrays grow automatically, but linked lists have a fixed size and inserting into them is expensive.

| | Human | System |
|---|---|---|
| Overall | 1.3 | 9.6 |
| (human correctness / relevance / completeness) | 0.5 / 4.5 / 0.5 | |

Keyword score for comparison: 8.2  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** Array and linked-list properties are exchanged (contiguous memory, constant-time access, fixed size), so humans gave 1.3. The system gave 9.6, the largest overestimate in the dataset; the keyword baseline was also fooled (8.2) because the same words appear. Both lexical and embedding methods measure overlap, not whether each statement is attributed to the right concept.

### Answer 85 — relevant_incorrect (Software Engineering)
**Question:** What is version control and why is it used?  
**Reference:** Version control records changes to files over time. It lets developers revert to earlier versions, compare changes, and work in parallel using branches. Git is a widely used distributed version control system.  
**AI answer:** Version control is a tool that compresses source code to make programs run faster. It keeps only the latest copy of each file, so you cannot go back to older versions, and Git is a centralized system that requires a single server.

| | Human | System |
|---|---|---|
| Overall | 0.8 | 8.7 |
| (human correctness / relevance / completeness) | 0.0 / 4.0 / 0.0 | |

Keyword score for comparison: 2.5  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** The answer claims version control compresses code and keeps no history, which is false, but it still scores 8.7. Here the keyword baseline was much closer to the humans (2.5) because the wrong answer uses different words (compress, faster) from the reference, while the embedding still sees the same topic. This shows the semantic baseline is more lenient than keyword matching on confident wrong answers.

### Answer 55 — relevant_incorrect (Artificial Intelligence)
**Question:** What is the A* search algorithm?  
**Reference:** A* is an informed search algorithm that finds the shortest path. It ranks nodes by f(n) = g(n) + h(n). g(n) is the cost from the start and h(n) is a heuristic estimate to the goal. A* is optimal when the heuristic is admissible.  
**AI answer:** A* is an uninformed search algorithm that explores nodes in random order. It ranks nodes only by h(n), the cost already travelled from the start, and it is guaranteed to find the shortest path even when the heuristic overestimates.

| | Human | System |
|---|---|---|
| Overall | 1.7 | 9.3 |
| (human correctness / relevance / completeness) | 0.5 / 6.5 / 0.5 | |

Keyword score for comparison: 5.8  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** A* is described as uninformed and random with an incorrect formula, yet it scores 9.3. Mentioning h(n), shortest path and heuristic is enough for a high embedding match. Technical terms that appear in both texts dominate the similarity even when their relationships are stated incorrectly.

### Answer 35 — relevant_incorrect (DBMS)
**Question:** Explain the ACID properties of transactions.  
**Reference:** ACID describes reliable database transactions. The properties are atomicity, consistency, isolation, and durability. Atomicity means all or nothing. Durability means committed changes survive failures.  
**AI answer:** ACID stands for accuracy, concurrency, integrity, and distribution. Atomicity means a transaction can be partly saved if an error happens, and durability means data is kept only until the server restarts.

| | Human | System |
|---|---|---|
| Overall | 1.3 | 8.7 |
| (human correctness / relevance / completeness) | 0.5 / 4.5 / 0.5 | |

Keyword score for comparison: 3.2  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** The ACID acronym is expanded incorrectly and atomicity and durability are defined backwards, so humans gave 1.3, but semantic similarity is 8.7. The answer stays entirely within the topic of database transactions, which is what the embedding captures. A fact-checking component, such as the LLM judge in the hybrid system, is needed to catch this.

### Answer 25 — relevant_incorrect (Computer Networks)
**Question:** Name the layers of the OSI model.  
**Reference:** The OSI model has seven layers. They are physical, data link, network, transport, session, presentation, and application. Each layer provides services to the layer above it.  
**AI answer:** The OSI model has five layers: physical, network, transport, session, and application. Each layer works independently and does not provide any services to the other layers.

| | Human | System |
|---|---|---|
| Overall | 2.7 | 9.2 |
| (human correctness / relevance / completeness) | 2.0 / 5.5 / 2.0 | |

Keyword score for comparison: 6.7  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** The answer says the OSI model has five layers and that layers do not serve each other. It lists real layer names, so it scores 9.2 against the reference. Humans disagreed somewhat on this answer (one rater gave relevance 8, another 3), but all of them rated correctness low; the system cannot separate on-topic from correct.

### Answer 75 — relevant_incorrect (Programming)
**Question:** What is a hash table?  
**Reference:** A hash table stores key-value pairs. A hash function maps each key to an index in an array. Collisions are handled by chaining or open addressing. Average time for insert, search, and delete is O(1).  
**AI answer:** A hash table stores values in sorted order and finds keys using binary search. Collisions cannot happen in a hash table, and the average time for searching is O(n log n).

| | Human | System |
|---|---|---|
| Overall | 2.6 | 8.8 |
| (human correctness / relevance / completeness) | 1.0 / 8.0 / 1.5 | |

Keyword score for comparison: 4.5  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** Saying hash tables are sorted, use binary search and have no collisions is wrong, but the vocabulary (key, search, collisions, average time) matches the reference, giving 8.8. Words like "cannot" in "collisions cannot happen" invert the meaning but hardly change the embedding.

### Answer 3 — partially_correct (Operating Systems)
**Question:** Explain deadlock in operating systems.  
**Reference:** Deadlock occurs when processes wait indefinitely for resources held by each other. It requires mutual exclusion, hold and wait, no preemption, and circular wait.  
**AI answer:** A deadlock is when processes get stuck and the system stops responding. It happens because of mutual exclusion on resources.

| | Human | System |
|---|---|---|
| Overall | 3.9 | 9.3 |
| (human correctness / relevance / completeness) | 3.5 / 7.5 / 2.5 | |

Keyword score for comparison: 3.9  
**Likely cause (auto, verify!):** missing content is not detected: a partial answer is still 'similar' to the reference  
**Your explanation:** The answer only gives a vague definition and one of the four deadlock conditions, so humans rated it about 4. Semantic similarity was still 9.3 because the main idea and the term "mutual exclusion" match the reference. Embeddings measure overall closeness, so missing content is not penalised; this is what Member 1's concept coverage is designed to catch.

### Answer 34 — correct_incomplete (DBMS)
**Question:** Explain the ACID properties of transactions.  
**Reference:** ACID describes reliable database transactions. The properties are atomicity, consistency, isolation, and durability. Atomicity means all or nothing. Durability means committed changes survive failures.  
**AI answer:** ACID is a set of properties that make database transactions reliable.

| | Human | System |
|---|---|---|
| Overall | 3.8 | 8.6 |
| (human correctness / relevance / completeness) | 3.5 / 9.0 / 1.5 | |

Keyword score for comparison: 4.2  
**Likely cause (auto, verify!):** missing content is not detected: a partial answer is still 'similar' to the reference  
**Your explanation:** "ACID is a set of properties that make database transactions reliable" is true but names none of the four properties. Humans scored completeness about 2, while semantic similarity was 8.6 because it closely paraphrases the reference's first sentence. A correct but incomplete summary looks almost identical to the full answer in embedding space.

### Answer 38 — hallucinated (DBMS)
**Question:** What is the difference between a primary key and a foreign key?  
**Reference:** A primary key uniquely identifies each row in a table and cannot be null. A foreign key is a column that refers to the primary key of another table. Foreign keys enforce referential integrity between tables.  
**AI answer:** A primary key uniquely identifies each row and cannot be null, while a foreign key refers to the primary key of another table and enforces referential integrity. A table can have at most one foreign key, and foreign keys automatically create a backup copy of the referenced table.

| | Human | System |
|---|---|---|
| Overall | 6.1 | 9.5 |
| (human correctness / relevance / completeness) | 5.5 / 8.5 / 5.5 | |

Keyword score for comparison: 7.6  
**Likely cause (auto, verify!):** embedding measures topic overlap, not truth: wrong facts on the right topic score high  
**Your explanation:** The core definitions of primary and foreign keys are correct, but two invented claims were added (at most one foreign key, automatic backups). Humans lowered correctness (overall 6.1) while the system gave 9.5, since added false sentences hardly reduce similarity when the rest matches. Hallucinated details are invisible to the semantic baseline.

### Answer 66 — irrelevant (Programming)
**Question:** What is the difference between an array and a linked list?  
**Reference:** An array stores elements in contiguous memory and allows constant-time access by index. A linked list stores nodes that point to the next node. Linked lists allow cheap insertion and deletion but need linear time to access an element. Arrays have a fixed size while linked lists grow dynamically.  
**AI answer:** A hash table stores key-value pairs and uses a hash function to map each key to an index.

| | Human | System |
|---|---|---|
| Overall | 0.0 | 3.2 |
| (human correctness / relevance / completeness) | 0.0 / 0.0 / 0.0 | |

Keyword score for comparison: 0.9  
**Likely cause (auto, verify!):** off-topic answer from the same subject area shares vocabulary with the reference  
**Your explanation:** This answer describes hash tables instead of comparing arrays and linked lists, so humans gave 0. It still received 3.2 because it comes from the same subject area and shares words like index and key. Similarity never drops to zero for same-domain text, so off-topic answers get some unearned credit.

### Answer 33 — partially_correct (DBMS)
**Question:** What is normalization in databases?  
**Reference:** Normalization organizes tables to reduce redundancy and avoid update, insertion, and deletion anomalies. It splits data into related tables linked by keys. Common normal forms are first normal form, second normal form, third normal form, and BCNF.  
**AI answer:** Normalization means organizing a database to reduce duplicate data. It involves first normal form.

| | Human | System |
|---|---|---|
| Overall | 5.3 | 8.5 |
| (human correctness / relevance / completeness) | 5.5 / 9.5 / 3.0 | |

Keyword score for comparison: 4.6  
**Likely cause (auto, verify!):** missing content is not detected: a partial answer is still 'similar' to the reference  
**Your explanation:** Mentioning only first normal form and "reducing duplicate data" covers part of the reference, so humans gave about 5. The system gave 8.5 because the answer is a short paraphrase of the reference's opening idea. As with other incomplete answers, the baseline cannot tell how much of the reference is actually covered.

### Answer 6 — irrelevant (Operating Systems)
**Question:** What is the difference between a process and a thread?  
**Reference:** A process is an independent program in execution with its own address space. A thread is a lightweight unit of execution inside a process. Threads of the same process share memory, open files, and code. Creating and switching threads is cheaper than creating and switching processes.  
**AI answer:** Virtual memory allows programs to use more memory than is physically available by swapping pages between RAM and disk.

| | Human | System |
|---|---|---|
| Overall | 0.0 | 3.1 |
| (human correctness / relevance / completeness) | 0.0 / 0.0 / 0.0 | |

Keyword score for comparison: 1.6  
**Likely cause (auto, verify!):** off-topic answer from the same subject area shares vocabulary with the reference  
**Your explanation:** This explains virtual memory in response to a question about processes and threads, so it is irrelevant (human 0). The system still gave 3.1 because both texts are about operating-system memory concepts. This is a smaller error than for wrong-but-relevant answers, but it shows that same-subject off-topic answers are not scored as zero.
