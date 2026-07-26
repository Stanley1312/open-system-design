from enum import Enum
from io import BytesIO
import time
import uuid

from flask import Flask, jsonify, render_template, request, send_file


app = Flask(__name__)

# V1 only: jobs live in one Python process and disappear when the server restarts.
job_storage: dict[str, dict] = {}

SYNC_EXPORT_DURATION_SECONDS = 10
DEFAULT_ASYNC_EXPORT_DURATION_SECONDS = 20
MAX_ASYNC_EXPORT_DURATION_SECONDS = 120


class Status(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"


@app.get("/")
def index():
    return render_template(
        "index.html",
        sync_duration=SYNC_EXPORT_DURATION_SECONDS,
        async_duration=DEFAULT_ASYNC_EXPORT_DURATION_SECONDS,
    )


@app.get("/sync-export")
def sync_export():
    """Simulate a slow DB query while the HTTP request remains open."""
    raw_duration = request.args.get(
        "time", default=str(SYNC_EXPORT_DURATION_SECONDS)
    )
    try:
        duration = int(raw_duration)
    except (TypeError, ValueError):
        return jsonify({"error": "time must be an integer between 1 and 120"}), 400

    if not 1 <= duration <= 120:
        return jsonify({"error": "time must be an integer between 1 and 120"}), 400

    time.sleep(duration)

    content = (
        "Sync export completed.\n"
        f"The simulated database query took {duration} seconds.\n"
    )
    return send_file(
        BytesIO(content.encode("utf-8")),
        mimetype="text/plain",
        as_attachment=True,
        download_name="sync-export.txt",
    )


@app.post("/async-export")
def create_async_export_job():
    """Create a simulated background job and return immediately."""
    payload = request.get_json(silent=True) or {}
    duration = payload.get(
        "duration_seconds", DEFAULT_ASYNC_EXPORT_DURATION_SECONDS
    )

    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not 1 <= duration <= MAX_ASYNC_EXPORT_DURATION_SECONDS
    ):
        return (
            jsonify(
                {
                    "error": (
                        "duration_seconds must be a number between "
                        f"1 and {MAX_ASYNC_EXPORT_DURATION_SECONDS}"
                    )
                }
            ),
            400,
        )

    job_id = str(uuid.uuid4())
    job_storage[job_id] = {
        "status": Status.RUNNING,
        "started_at": time.time(),
        "duration": duration,
    }

    return (
        jsonify(
            {
                "job_id": job_id,
                "status": Status.RUNNING,
                "duration_seconds": duration,
            }
        ),
        202,
    )


@app.get("/async-export/<job_id>/status")
def async_export_status(job_id: str):
    job = job_storage.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    elapsed = time.time() - job["started_at"]
    progress = min(100, int(elapsed / job["duration"] * 100))

    if progress >= 100:
        job["status"] = Status.COMPLETED

    return jsonify(
        {
            "job_id": job_id,
            "status": job["status"],
            "progress": progress,
        }
    )


@app.get("/async-export/<job_id>/download")
def download_async_export(job_id: str):
    job = job_storage.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    if job["status"] != Status.COMPLETED:
        return (
            jsonify(
                {
                    "job_id": job_id,
                    "status": job["status"],
                    "error": "Export is not ready",
                }
            ),
            409,
        )

    content = (
        "Async export completed.\n"
        f"Job ID: {job_id}\n"
        f"The simulated worker took {job['duration']} seconds.\n"
    )
    return send_file(
        BytesIO(content.encode("utf-8")),
        mimetype="text/plain",
        as_attachment=True,
        download_name="async-export.txt",
    )
