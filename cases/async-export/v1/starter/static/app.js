const form = document.querySelector("#sync-form");
const durationInput = document.querySelector("#duration");
const timer = document.querySelector("#timer");
const status = document.querySelector("#status");
const submitButton = form.querySelector("button");

function formatElapsed(totalSeconds) {
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

async function downloadResponse(response) {
  if (!response.ok) {
    const body = await response.json();
    throw new Error(body.error || `Request failed (${response.status})`);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = "sync-export.txt";
  link.click();
  URL.revokeObjectURL(objectUrl);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const duration = Number(durationInput.value);
  if (!Number.isInteger(duration) || duration < 1 || duration > 120) {
    status.textContent = "Enter a whole number from 1 to 120.";
    durationInput.focus();
    return;
  }

  submitButton.disabled = true;
  durationInput.disabled = true;
  status.textContent =
    "Waiting… the server has not returned a file or progress yet.";
  timer.textContent = "00:00";

  const startedAt = Date.now();
  const timerId = window.setInterval(() => {
    timer.textContent = formatElapsed(
      Math.floor((Date.now() - startedAt) / 1000),
    );
  }, 250);

  try {
    const query = new URLSearchParams({ time: String(duration) });
    const response = await fetch(`/sync-export?${query}`);
    await downloadResponse(response);
    status.textContent =
      "Complete. The response arrived only after all work had finished.";
  } catch (error) {
    status.textContent = error.message;
  } finally {
    window.clearInterval(timerId);
    timer.textContent = formatElapsed(
      Math.floor((Date.now() - startedAt) / 1000),
    );
    submitButton.disabled = false;
    durationInput.disabled = false;
  }
});
