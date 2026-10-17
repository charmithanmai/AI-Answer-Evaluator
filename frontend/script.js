const API_URL = "http://127.0.0.1:8000/evaluate";

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