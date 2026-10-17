const form = document.getElementById("evaluate-form");
const errorMessage = document.getElementById("error-message");

form.addEventListener("submit", function (event) {
  event.preventDefault(); // stop the page from reloading

  const question = document.getElementById("question").value.trim();
  const referenceAnswer = document.getElementById("reference_answer").value.trim();
  const aiAnswer = document.getElementById("ai_answer").value.trim();

  // Simple check: no empty fields
  if (!question || !referenceAnswer || !aiAnswer) {
    errorMessage.textContent = "Please fill in all three fields.";
    return;
  }
  errorMessage.textContent = "";

  const payload = {
    question: question,
    reference_answer: referenceAnswer,
    ai_answer: aiAnswer,
  };

  console.log("Data to send to /evaluate:", payload);
});