const API_URL = "http://127.0.0.1:8000/evaluate";
const HISTORY_URL = "http://127.0.0.1:8000/history";

const form = document.getElementById("evaluate-form");
const errorMessage = document.getElementById("error-message");
const resultsSection = document.getElementById("results");
const evaluateButton = document.getElementById("evaluate-btn");

// ---------- Helpers ----------

// Returns "good", "medium" or "low" for a score out of 10
function scoreLevel(score) {
  if (score >= 7) return "good";
  if (score >= 4) return "medium";
  return "low";
}

// Writes the text of a result card and fills its progress bar
function setCard(id, text, fraction) {
  document.getElementById(id).textContent = text;

  const percent = Math.max(0, Math.min(1, fraction)) * 100;
  const bar = document.getElementById(id + "-bar");
  bar.style.width = percent + "%";
  bar.classList.remove("fill-good", "fill-medium", "fill-low");
  bar.classList.add("fill-" + scoreLevel(fraction * 10));
}

// ---------- Results dashboard ----------

function showResults(result) {
  setCard("correctness", result.correctness + "/10", result.correctness / 10);
  setCard("relevance", result.relevance + "/10", result.relevance / 10);
  setCard("completeness", result.completeness + "/10", result.completeness / 10);
  setCard("semantic-similarity", result.semantic_similarity.toFixed(2), result.semantic_similarity);
  setCard("concept-coverage", Math.round(result.concept_coverage * 100) + "%", result.concept_coverage);

  const overall = document.getElementById("overall-score");
  overall.textContent = result.overall_score + "/10";
  overall.classList.remove("score-good", "score-medium", "score-low");
  overall.classList.add("score-" + scoreLevel(result.overall_score));

  document.getElementById("feedback-text").textContent = result.feedback;

  resultsSection.classList.remove("hidden");
  resultsSection.scrollIntoView({ behavior: "smooth" });
}

// ---------- Submit ----------

form.addEventListener("submit", async function (event) {
  event.preventDefault(); // stop the page from reloading

  const question = document.getElementById("question").value.trim();
  const referenceAnswer = document.getElementById("reference_answer").value.trim();
  const aiAnswer = document.getElementById("ai_answer").value.trim();

  if (!question || !referenceAnswer || !aiAnswer) {
    errorMessage.textContent = "Please fill in all three fields.";
    resultsSection.classList.add("hidden");
    return;
  }
  errorMessage.textContent = "";

  const payload = {
    question: question,
    reference_answer: referenceAnswer,
    ai_answer: aiAnswer,
  };

  // Loading state
  evaluateButton.disabled = true;
  evaluateButton.classList.add("loading");
  evaluateButton.textContent = "Evaluating...";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("The server returned an error (status " + response.status + ").");
    }

    const result = await response.json();
    showResults(result);
    loadHistory();
  } catch (error) {
    console.error(error);
    errorMessage.textContent =
      "Could not evaluate the answer. Make sure the backend is running. (" + error.message + ")";
    resultsSection.classList.add("hidden");
  } finally {
    evaluateButton.disabled = false;
    evaluateButton.classList.remove("loading");
    evaluateButton.textContent = "EVALUATE";
  }
});

// ---------- Day 8: Example, Clear Form, Ctrl + Enter ----------

const EXAMPLE = {
  question: "Explain deadlock in operating systems.",
  reference_answer:
    "Deadlock occurs when processes wait indefinitely for resources held by each other. " +
    "It requires mutual exclusion, hold and wait, no preemption, and circular wait.",
  ai_answer:
    "Deadlock occurs when two or more processes wait for resources held by one another, " +
    "so none can proceed.",
};

document.getElementById("example-btn").addEventListener("click", function () {
  document.getElementById("question").value = EXAMPLE.question;
  document.getElementById("reference_answer").value = EXAMPLE.reference_answer;
  document.getElementById("ai_answer").value = EXAMPLE.ai_answer;
  errorMessage.textContent = "";
});

document.getElementById("clear-form-btn").addEventListener("click", function () {
  form.reset();
  errorMessage.textContent = "";
  resultsSection.classList.add("hidden");
});

form.addEventListener("keydown", function (event) {
  if (event.ctrlKey && event.key === "Enter") {
    form.requestSubmit();
  }
});

// ---------- History ----------

function formatTime(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString();
}

function addDetail(parent, label, value) {
  const line = document.createElement("p");
  const strong = document.createElement("strong");
  strong.textContent = label + ": ";
  line.appendChild(strong);
  line.appendChild(document.createTextNode(value));
  parent.appendChild(line);
}

async function loadHistory() {
  const list = document.getElementById("history-list");
  const emptyMessage = document.getElementById("history-empty");
  const count = document.getElementById("history-count");

  try {
    const response = await fetch(HISTORY_URL);
    if (!response.ok) {
      throw new Error("History could not be loaded.");
    }
    const items = await response.json();

    list.innerHTML = "";
    emptyMessage.textContent = "No evaluations yet.";
    emptyMessage.classList.toggle("hidden", items.length > 0);
    count.textContent = items.length > 0 ? "(" + items.length + ")" : "";

    items.forEach(function (item) {
      const details = document.createElement("details");
      details.className = "history-item";

      const summary = document.createElement("summary");

      const badge = document.createElement("span");
      badge.className = "badge badge-" + scoreLevel(item.overall_score);
      badge.textContent = item.overall_score + "/10";

      const shortQuestion =
        item.question.length > 60 ? item.question.slice(0, 60) + "..." : item.question;
      const label = document.createElement("span");
      label.textContent = formatTime(item.created_at) + "  |  " + shortQuestion;

      summary.appendChild(badge);
      summary.appendChild(label);
      details.appendChild(summary);

      const body = document.createElement("div");
      body.className = "history-body";
      addDetail(body, "Question", item.question);
      addDetail(body, "Reference Answer", item.reference_answer);
      addDetail(body, "AI Answer", item.ai_answer);
      addDetail(
        body,
        "Scores",
        "Correctness " + item.correctness + "/10, Relevance " + item.relevance +
          "/10, Completeness " + item.completeness + "/10, Semantic Similarity " +
          Number(item.semantic_similarity).toFixed(2) + ", Concept Coverage " +
          Math.round(item.concept_coverage * 100) + "%"
      );
      if (item.missing_concepts && item.missing_concepts.length > 0) {
        addDetail(body, "Missing concepts", item.missing_concepts.join(", "));
      }
      addDetail(body, "Feedback", item.feedback);
      details.appendChild(body);

      list.appendChild(details);
    });
  } catch (error) {
    console.error(error);
    emptyMessage.textContent = "History could not be loaded. Is the backend running?";
    emptyMessage.classList.remove("hidden");
  }
}

document.getElementById("refresh-history").addEventListener("click", loadHistory);

document.getElementById("clear-history").addEventListener("click", async function () {
  if (!confirm("Delete all saved evaluations? This cannot be undone.")) {
    return;
  }
  try {
    const response = await fetch(HISTORY_URL, { method: "DELETE" });
    if (!response.ok) {
      throw new Error("Could not clear history.");
    }
    loadHistory();
  } catch (error) {
    console.error(error);
    alert("Could not clear history. Is the backend running?");
  }
});

loadHistory(); // show past evaluations when the page opens
