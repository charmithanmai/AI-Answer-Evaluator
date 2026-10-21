const API_URL = "http://127.0.0.1:8000/evaluate";
const HISTORY_URL = "http://127.0.0.1:8000/history";
const form = document.getElementById("evaluate-form");
const errorMessage = document.getElementById("error-message");
const resultsSection = document.getElementById("results");
const evaluateButton = document.getElementById("evaluate-btn");

function showResults(result) {
  document.getElementById("overall-score").textContent = result.overall_score + "/10";
  document.getElementById("correctness").textContent = result.correctness + "/10";
  document.getElementById("relevance").textContent = result.relevance + "/10";
  document.getElementById("completeness").textContent = result.completeness + "/10";
  document.getElementById("semantic-similarity").textContent = result.semantic_similarity.toFixed(2);
  document.getElementById("concept-coverage").textContent = Math.round(result.concept_coverage * 100) + "%";
  document.getElementById("feedback-text").textContent = result.feedback;
    const conceptsSummary = document.getElementById("concepts-summary");
  const missingList = document.getElementById("missing-list");
  missingList.innerHTML = "";
  if (result.concepts_total) {
    conceptsSummary.textContent =
      result.concepts_covered + " of " + result.concepts_total + " key concepts covered.";
  } else {
    conceptsSummary.textContent = "";
  }
  (result.missing_concepts || []).forEach(function (concept) {
    const item = document.createElement("li");
    item.textContent = "Missing: " + concept;
    missingList.appendChild(item);
  });
  // Colour the overall score: green / orange / red
  const overall = document.getElementById("overall-score");
  overall.classList.remove("score-good", "score-medium", "score-low");
  if (result.overall_score >= 7) {
    overall.classList.add("score-good");
  } else if (result.overall_score >= 4) {
    overall.classList.add("score-medium");
  } else {
    overall.classList.add("score-low");
  }

  resultsSection.classList.remove("hidden");
  resultsSection.scrollIntoView({ behavior: "smooth" });
}

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
    evaluateButton.textContent = "EVALUATE";
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

  try {
    const response = await fetch(HISTORY_URL);
    if (!response.ok) {
      throw new Error("History could not be loaded.");
    }
    const items = await response.json();

    list.innerHTML = "";
    emptyMessage.classList.toggle("hidden", items.length > 0);

    items.forEach(function (item) {
      const details = document.createElement("details");
      details.className = "history-item";

      const summary = document.createElement("summary");
      const shortQuestion =
        item.question.length > 60 ? item.question.slice(0, 60) + "..." : item.question;
      summary.textContent =
        formatTime(item.created_at) + "  |  " + shortQuestion + "  |  " + item.overall_score + "/10";
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

loadHistory(); // show past evaluations when the page opens
