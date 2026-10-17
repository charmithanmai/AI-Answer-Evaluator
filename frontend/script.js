const form = document.getElementById("evaluate-form");
const errorMessage = document.getElementById("error-message");
const resultsSection = document.getElementById("results");

// Fake result used until the real evaluator is connected (Day 6)
const mockResult = {
  correctness: 8,
  relevance: 9,
  completeness: 7,
  semantic_similarity: 0.86,
  concept_coverage: 0.75,
  overall_score: 8.1,
  feedback: "The answer is mostly correct but misses an important concept.",
};

function showResults(result) {
  document.getElementById("overall-score").textContent = result.overall_score + "/10";
  document.getElementById("correctness").textContent = result.correctness + "/10";
  document.getElementById("relevance").textContent = result.relevance + "/10";
  document.getElementById("completeness").textContent = result.completeness + "/10";
  document.getElementById("semantic-similarity").textContent = result.semantic_similarity.toFixed(2);
  document.getElementById("concept-coverage").textContent = Math.round(result.concept_coverage * 100) + "%";
  document.getElementById("feedback-text").textContent = result.feedback;

  resultsSection.classList.remove("hidden");
  resultsSection.scrollIntoView({ behavior: "smooth" });
}

form.addEventListener("submit", function (event) {
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
  console.log("Data to send to /evaluate:", payload);

  // For now we show the mock JSON. On Day 4 this becomes a call to the API.
  showResults(mockResult);
});