const syncButton = document.querySelector("#sync-start");
const syncTimer = document.querySelector("#sync-timer");
const syncStatus = document.querySelector("#sync-status");
const syncDuration = document.querySelector("#sync-duration");

const asyncButton = document.querySelector("#async-start");
const asyncStatus = document.querySelector("#async-status");
const asyncPercent = document.querySelector("#async-percent");
const asyncProgress = document.querySelector("#async-progress");
const asyncProgressFill = document.querySelector("#async-progress-fill");
const pollingNote = document.querySelector("#polling-note");
const asyncDuration = document.querySelector("#async-duration");

function formatElapsed(totalSeconds) {
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function filenameFrom(response, fallback) {
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/i);
  return match?.[1] || fallback;
}

async function saveResponseAsFile(response, fallbackName) {
  if (!response.ok) {
    throw new Error(`Download failed (${response.status})`);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filenameFrom(response, fallbackName);
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

syncButton.addEventListener("click", async () => {
  const durationSeconds = Number(syncDuration.value);
  if (
    !Number.isFinite(durationSeconds) ||
    durationSeconds < 1 ||
    durationSeconds > 120
  ) {
    syncStatus.textContent = "Enter a duration between 1 and 120 seconds";
    syncDuration.focus();
    return;
  }

  syncButton.disabled = true;
  syncDuration.disabled = true;
  syncStatus.textContent = "Request open · waiting for server response…";

  const startedAt = Date.now();
  const timerId = window.setInterval(() => {
    const seconds = Math.floor((Date.now() - startedAt) / 1000);
    syncTimer.textContent = formatElapsed(seconds);
  }, 250);

  try {
    const query = new URLSearchParams({ time: String(durationSeconds) });
    const response = await fetch(`/sync-export?${query}`);
    await saveResponseAsFile(response, "sync-export.txt");
    syncStatus.textContent = "Complete · file downloaded";
  } catch (error) {
    syncStatus.textContent = error.message;
  } finally {
    window.clearInterval(timerId);
    const seconds = Math.floor((Date.now() - startedAt) / 1000);
    syncTimer.textContent = formatElapsed(seconds);
    syncButton.disabled = false;
    syncDuration.disabled = false;
  }
});

function renderProgress(progress, status) {
  asyncPercent.textContent = `${progress}%`;
  asyncProgressFill.style.width = `${progress}%`;
  asyncProgress.setAttribute("aria-valuenow", String(progress));
  asyncStatus.textContent =
    status === "completed" ? "Finished · downloading…" : "Worker processing";
}

async function getJobStatus(jobId) {
  const response = await fetch(`/async-export/${jobId}/status`);
  if (!response.ok) {
    throw new Error(`Could not read job status (${response.status})`);
  }
  return response.json();
}

async function waitForJob(jobId, pollIntervalMs) {
  while (true) {
    const job = await getJobStatus(jobId);
    renderProgress(job.progress, job.status);

    if (job.status === "completed") {
      return;
    }

    pollingNote.textContent =
      `Next status check in ${pollIntervalMs / 1000} seconds`;
    await new Promise((resolve) => window.setTimeout(resolve, pollIntervalMs));
  }
}

asyncButton.addEventListener("click", async () => {
  const durationSeconds = Number(asyncDuration.value);
  if (
    !Number.isFinite(durationSeconds) ||
    durationSeconds < 1 ||
    durationSeconds > 120
  ) {
    asyncStatus.textContent = "Invalid duration";
    pollingNote.textContent = "Enter a duration between 1 and 120 seconds";
    asyncDuration.focus();
    return;
  }

  // Short jobs need faster feedback; never poll more than once per second.
  const pollIntervalMs = Math.max(
    1_000,
    Math.min(10_000, Math.round(durationSeconds / 10) * 1_000),
  );

  asyncButton.disabled = true;
  asyncDuration.disabled = true;
  asyncProgress.closest(".progress-section").classList.add("is-polling");
  renderProgress(0, "running");
  pollingNote.textContent = "Creating export job…";

  try {
    const createResponse = await fetch("/async-export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ duration_seconds: durationSeconds }),
    });
    if (!createResponse.ok) {
      throw new Error(`Could not create export job (${createResponse.status})`);
    }

    const job = await createResponse.json();
    pollingNote.textContent =
      `Job ${job.job_id.slice(0, 8)} · polling every ${pollIntervalMs / 1000}s`;
    await waitForJob(job.job_id, pollIntervalMs);

    const downloadResponse = await fetch(
      `/async-export/${job.job_id}/download`,
    );
    await saveResponseAsFile(downloadResponse, "async-export.txt");
    asyncStatus.textContent = "Finished · file downloaded";
    pollingNote.textContent = "Export flow completed successfully";
  } catch (error) {
    asyncStatus.textContent = "Export failed";
    pollingNote.textContent = error.message;
  } finally {
    asyncProgress.closest(".progress-section").classList.remove("is-polling");
    asyncButton.disabled = false;
    asyncDuration.disabled = false;
  }
});
