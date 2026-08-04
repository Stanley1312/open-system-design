const POLL_INTERVAL_MS = 1000;

const elements = {
  apiState: document.querySelector("#api-state"),
  apiDot: document.querySelector("#api-dot"),
  databaseState: document.querySelector("#database-state"),
  databaseDot: document.querySelector("#database-dot"),
  poolSummary: document.querySelector("#pool-summary"),
  completedSummary: document.querySelector("#completed-summary"),
  pendingCount: document.querySelector("#pending-count"),
  runningCount: document.querySelector("#running-count"),
  completedCount: document.querySelector("#completed-count"),
  errorCount: document.querySelector("#error-count"),
  workerGrid: document.querySelector("#worker-grid"),
  timeline: document.querySelector("#timeline"),
  jobsBody: document.querySelector("#jobs-body"),
  jobForm: document.querySelector("#job-form"),
  durationInput: document.querySelector("#duration-input"),
  jobCountInput: document.querySelector("#job-count-input"),
  createButton: document.querySelector("#create-button"),
  createNote: document.querySelector("#create-note"),
  workerForm: document.querySelector("#worker-form"),
  workerInput: document.querySelector("#worker-count-input"),
  workerMinus: document.querySelector("#worker-minus"),
  workerPlus: document.querySelector("#worker-plus"),
  configuredWorkers: document.querySelector("#configured-workers"),
  cpuLimit: document.querySelector("#cpu-limit"),
  workerNote: document.querySelector("#worker-note"),
  filters: document.querySelector("#job-filters"),
};

let previousJobs = new Map();
let timelineEvents = [];
let activeFilter = "all";
let latestState = null;
let workerInputDirty = false;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function shortId(jobId) {
  return jobId.slice(0, 8);
}

function clockTime(date) {
  return new Intl.DateTimeFormat([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date || new Date());
}

function plural(count, word) {
  return count + " " + word + (count === 1 ? "" : "s");
}

function addEvent(message, tone) {
  timelineEvents.unshift({
    time: clockTime(),
    message: message,
    tone: tone || "",
  });
  timelineEvents = timelineEvents.slice(0, 30);
  elements.timeline.innerHTML = timelineEvents
    .map(function (event) {
      return (
        '<li class="' +
        escapeHtml(event.tone) +
        '">' +
        "<time>" +
        escapeHtml(event.time) +
        "</time>" +
        "<span>" +
        escapeHtml(event.message) +
        "</span>" +
        "</li>"
      );
    })
    .join("");
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(function () {
    return {};
  });
  if (!response.ok) {
    throw new Error(
      payload.error || "Request failed (" + response.status + ")",
    );
  }
  return payload;
}

function renderSystem(system) {
  const counts = system.jobs;
  elements.apiState.textContent = "Online";
  elements.apiDot.classList.toggle("is-offline", system.api !== "online");
  elements.databaseState.textContent =
    system.database === "connected" ? "Connected" : "Unavailable";
  elements.databaseDot.classList.toggle(
    "is-offline",
    system.database !== "connected",
  );
  elements.poolSummary.textContent =
    system.live_workers + " live / " + system.configured_workers + " set";
  elements.completedSummary.textContent = plural(counts.completed, "file");
  elements.pendingCount.textContent = counts.pending;
  elements.runningCount.textContent = counts.running;
  elements.completedCount.textContent = counts.completed;
  elements.errorCount.textContent = counts.error;
  elements.configuredWorkers.textContent = system.configured_workers;
  elements.cpuLimit.textContent = system.worker_limit;
  elements.workerInput.max = system.worker_limit;

  if (!workerInputDirty) {
    elements.workerInput.value = system.configured_workers;
  }
}

function workerCard(worker) {
  let body;
  if (worker.job) {
    body =
      '<div class="worker-job"><span>Job ' +
      escapeHtml(shortId(worker.job.job_id)) +
      "</span><strong>" +
      worker.job.progress +
      "%</strong></div>" +
      '<div class="mini-progress"><i style="width:' +
      worker.job.progress +
      '%"></i></div>' +
      "<small>" +
      worker.job.duration_seconds +
      "s export · PID " +
      worker.pid +
      "</small>";
  } else {
    const message =
      worker.status === "draining"
        ? "Stopping before the next claim"
        : "Waiting for a pending job";
    body =
      '<p class="worker-idle">' +
      message +
      "</p><small>PID " +
      worker.pid +
      "</small>";
  }

  return (
    '<article class="worker-card is-' +
    escapeHtml(worker.status) +
    '">' +
    '<div class="worker-card-heading"><strong>Worker ' +
    worker.worker_id +
    "</strong><span>" +
    escapeHtml(worker.status) +
    "</span></div>" +
    body +
    "</article>"
  );
}

function renderWorkers(workers) {
  elements.workerGrid.innerHTML = workers.length
    ? workers.map(workerCard).join("")
    : '<p class="empty-state">No live workers.</p>';
}

function statusPill(status) {
  return (
    '<span class="status-pill is-' +
    escapeHtml(status) +
    '">' +
    escapeHtml(status) +
    "</span>"
  );
}

function jobRow(job) {
  let action = "—";
  if (job.status === "completed") {
    action =
      '<button class="download-link" data-download="' +
      escapeHtml(job.job_id) +
      '">Download ↓</button>';
  } else if (job.status === "error") {
    action =
      '<span class="error-hint" title="' +
      escapeHtml(job.error || "Unknown error") +
      '">View error</span>';
  }

  return (
    "<tr><td><code>" +
    escapeHtml(shortId(job.job_id)) +
    "</code></td><td>" +
    statusPill(job.status) +
    "</td><td>" +
    (job.worker_id === null ? "—" : "Worker " + job.worker_id) +
    "</td><td>" +
    job.duration_seconds +
    's</td><td><div class="table-progress"><span><i style="width:' +
    job.progress +
    '%"></i></span><small>' +
    job.progress +
    "%</small></div></td><td>" +
    escapeHtml(clockTime(new Date(job.created_at))) +
    "</td><td>" +
    action +
    "</td></tr>"
  );
}

function renderJobs(jobs) {
  const visibleJobs =
    activeFilter === "all"
      ? jobs
      : jobs.filter(function (job) {
          return job.status === activeFilter;
        });

  elements.jobsBody.innerHTML = visibleJobs.length
    ? visibleJobs.map(jobRow).join("")
    : '<tr><td colspan="7" class="empty-state">No matching jobs.</td></tr>';
}

function observeJobChanges(jobs) {
  const currentJobs = new Map(
    jobs.map(function (job) {
      return [job.job_id, job];
    }),
  );

  if (previousJobs.size > 0) {
    jobs.forEach(function (job) {
      const previous = previousJobs.get(job.job_id);
      if (!previous) {
        addEvent("Job " + shortId(job.job_id) + " entered the pending queue");
      } else if (previous.status !== job.status) {
        if (job.status === "running") {
          addEvent(
            "Worker " + job.worker_id + " claimed job " + shortId(job.job_id),
            "is-running",
          );
        } else if (job.status === "completed") {
          addEvent(
            "Job " + shortId(job.job_id) + " is ready to download",
            "is-success",
          );
        } else if (job.status === "error") {
          addEvent("Job " + shortId(job.job_id) + " failed", "is-error");
        }
      }
    });
  }
  previousJobs = currentJobs;
}

function renderDashboard(state) {
  latestState = state;
  renderSystem(state.system);
  renderWorkers(state.workers);
  observeJobChanges(state.jobs);
  renderJobs(state.jobs);
}

async function refreshDashboard() {
  try {
    renderDashboard(await requestJson("/demo/dashboard"));
  } catch (error) {
    elements.apiState.textContent = "Unavailable";
    elements.apiDot.classList.add("is-offline");
    if (
      !timelineEvents.some(function (event) {
        return event.message === error.message;
      })
    ) {
      addEvent(error.message, "is-error");
    }
  }
}

elements.jobForm.addEventListener("submit", async function (event) {
  event.preventDefault();
  const duration = Number(elements.durationInput.value);
  const count = Number(elements.jobCountInput.value);

  if (!Number.isInteger(duration) || duration < 1 || duration > 120) {
    elements.createNote.textContent =
      "Duration must be an integer from 1 to 120.";
    elements.durationInput.focus();
    return;
  }
  if (!Number.isInteger(count) || count < 1 || count > 20) {
    elements.createNote.textContent = "Create between 1 and 20 jobs.";
    elements.jobCountInput.focus();
    return;
  }

  elements.createButton.disabled = true;
  elements.createNote.textContent = "Creating " + plural(count, "job") + "…";

  try {
    await Promise.all(
      Array.from({ length: count }, function () {
        return requestJson("/async-export", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ duration_seconds: duration }),
        });
      }),
    );
    elements.createNote.textContent =
      plural(count, "job") + " accepted with HTTP 202.";
    addEvent(plural(count, "export job") + " created", "is-success");
    await refreshDashboard();
  } catch (error) {
    elements.createNote.textContent = error.message;
    addEvent(error.message, "is-error");
  } finally {
    elements.createButton.disabled = false;
  }
});

elements.workerForm.addEventListener("submit", async function (event) {
  event.preventDefault();
  const count = Number(elements.workerInput.value);
  const limit = Number(elements.workerInput.max);

  if (!Number.isInteger(count) || count < 1 || count > limit) {
    elements.workerNote.textContent =
      "Choose an integer from 1 to " + limit + ".";
    elements.workerInput.focus();
    return;
  }

  elements.workerNote.textContent = "Applying worker pool size…";
  try {
    const result = await requestJson("/demo/workers", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count: count }),
    });
    workerInputDirty = false;
    elements.workerInput.value = result.configured_workers;
    elements.workerNote.textContent =
      "Pool target changed to " + plural(count, "worker") + ".";
    addEvent("Worker pool target changed to " + count);
    await refreshDashboard();
  } catch (error) {
    elements.workerNote.textContent = error.message;
    addEvent(error.message, "is-error");
  }
});

elements.workerInput.addEventListener("input", function () {
  workerInputDirty = true;
});

elements.workerMinus.addEventListener("click", function () {
  workerInputDirty = true;
  elements.workerInput.value = Math.max(
    1,
    Number(elements.workerInput.value) - 1,
  );
});

elements.workerPlus.addEventListener("click", function () {
  workerInputDirty = true;
  elements.workerInput.value = Math.min(
    Number(elements.workerInput.max),
    Number(elements.workerInput.value) + 1,
  );
});

elements.filters.addEventListener("click", function (event) {
  const button = event.target.closest("button[data-status]");
  if (!button) return;

  activeFilter = button.dataset.status;
  elements.filters.querySelectorAll("button").forEach(function (item) {
    item.classList.toggle("is-active", item === button);
  });
  if (latestState) renderJobs(latestState.jobs);
});

elements.jobsBody.addEventListener("click", async function (event) {
  const button = event.target.closest("button[data-download]");
  if (!button) return;

  try {
    const response = await fetch(
      "/async-export/" + button.dataset.download + "/download",
    );
    if (!response.ok) {
      const payload = await response.json().catch(function () {
        return {};
      });
      throw new Error(
        payload.error || "Download failed (" + response.status + ")",
      );
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = "async-export-" + button.dataset.download + ".txt";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
    addEvent(
      "Downloaded job " + shortId(button.dataset.download),
      "is-success",
    );
  } catch (error) {
    addEvent(error.message, "is-error");
  }
});

addEvent("Dashboard connected");
refreshDashboard();
window.setInterval(refreshDashboard, POLL_INTERVAL_MS);
