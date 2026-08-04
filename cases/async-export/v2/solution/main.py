from enum import Enum
from io import BytesIO
import time
import uuid
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request, send_file
from multiprocessing import Process

from db import get_connection, get_job, update_job


app = Flask(__name__)

SYNC_EXPORT_DURATION_SECONDS = 10
DEFAULT_ASYNC_EXPORT_DURATION_SECONDS = 20
MAX_ASYNC_EXPORT_DURATION_SECONDS = 120


class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


@app.get("/")
def index():
    return render_template(
        "index.html",
        sync_duration=SYNC_EXPORT_DURATION_SECONDS,
        async_duration=DEFAULT_ASYNC_EXPORT_DURATION_SECONDS,
    )


def run_job(job):
    print(f"Run job={job['job_id']} !.")
    job_duration = job["duration"]

    if job_duration > 0:
        print(f"Start run job for job ID={job['job_id']} !.")
        time.sleep(job_duration)
        return f"""
                This is the result of a sucessfull job,
                with job_id is {job["job_id"]},
                and the duration is {job["duration"]}.
            """

    else:
        raise ValueError("Job duration is less or equal than 0")


@app.post("/async-export")
def create_async_export_job():
    """Create a simulated background job and return immediately."""
    payload = request.get_json(silent=True) or {}
    duration = payload.get("duration_seconds", DEFAULT_ASYNC_EXPORT_DURATION_SECONDS)

    if (
        isinstance(duration, bool)
        or not isinstance(duration, int)
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
    try:
        with get_connection() as connection:
            job = connection.execute(
                """
                    INSERT INTO jobs (job_id, status, duration)
                    values(%s, %s, %s)
                    RETURNING job_id
                """,
                (job_id, Status.PENDING, duration),
            )

            job = job.fetchone()

            if job is None:
                return (
                    jsonify({"error": ("Can't create job.")}),
                    400,
                )
    except Exception as error:
        return {
            "error": f"Database error: {str(error)}",
        }, 500

    return (
        jsonify(
            {
                "job_id": job_id,
                "status": Status.PENDING,
                "duration_seconds": duration,
            }
        ),
        202,
    )


@app.get("/async-export/<job_id>/status")
def async_export_status(job_id: str):
    with get_connection() as connnection:
        job = get_job(connnection, job_id)

    if job is None:
        return jsonify({"error": "Job not found"}), 404
    if job["status"] == Status.PENDING:
        progress = 0
    elif job["status"] == Status.RUNNING:
        elapsed = (datetime.now(timezone.utc) - job["started_at"]).total_seconds()
        progress = min(99, int(elapsed / job["duration"] * 100))
    else:
        progress = 0

    return jsonify(
        {
            "job_id": job_id,
            "status": job["status"],
            "progress": progress,
        }
    ), 200


@app.get("/async-export/<job_id>/download")
def download_async_export(job_id: str):
    with get_connection() as connnection:
        job = get_job(connnection, job_id)
        if job is None:
            return jsonify({"error": "Job not found"}), 404
    if job["status"] == Status.ERROR:
        return jsonify(
            {
                "job_id": job_id,
                "status": job["status"],
                "error": job["error"],
            }
        ), 422

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

    return send_file(
        BytesIO(job["result"].encode("utf-8")),
        mimetype="text/plain",
        as_attachment=True,
        download_name=f"async-export-{job_id}.txt",
    )


if __name__ == "__main__":
    from worker import worker
    from db import process_job

    cpu_count = os.cpu_count() or 1

    workers = [
        Process(
            target=worker,
            args=(worker_id, process_job, run_job, update_job),
            name=f"worker-{worker_id}",
        )
        for worker_id in range(2)
    ]

    for process in workers:
        process.start()

    app.run()
