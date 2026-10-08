"use strict";
const input = document.getElementById("api-input");
const statusText = document.getElementById("api-status");
document.getElementById("api-load").addEventListener("click", async () => {
  try {
    const response = await fetch("/api/example");
    if (!response.ok) throw new Error("Could not load demo input.");
    input.value = JSON.stringify(await response.json(), null, 2);
    statusText.textContent = "Historical example loaded.";
  } catch (error) {
    statusText.textContent = error.message;
  }
});
document
  .getElementById("api-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = document.getElementById("api-submit");
    button.disabled = true;
    try {
      const payload = JSON.parse(input.value);
      const response = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      document.getElementById("api-output").textContent = JSON.stringify(
        await response.json(),
        null,
        2,
      );
      statusText.textContent = `HTTP ${response.status}`;
    } catch (error) {
      statusText.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
