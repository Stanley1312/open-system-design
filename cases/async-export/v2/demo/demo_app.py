"""Observable Flask app for the Async Export V2 teaching demo.

The owner implementation lives unchanged in ../solution. This app follows the
same job flow and adds read APIs plus worker-pool controls for visualization.
"""

import atexit
import os
from datetime import UTC, datetime
from io import BytesIO

import psycopg
from flask import Flask, jsonify, render_template, request, send_file

import demo_db
from worker_pool import WorkerPool

DEFAULT_DURATION_SECONDS = 20
MAX_DURATION_SECONDS = 120
DEFAULT_WORKERS = int(os.getenv("DEFAULT_WORKERS", "2"))

app = Flask(__name__)
worker_pool = WorkerPool(DEFAULT_WORKERS)


def calculate_progress(job) -> int:
    if job["status"] == "pending":
        return 0
    if job["status"] == "completed":
        return 100
    if job["status"] == "error":
        return 0
    if job["started_at"] is None:
        return 0

    elapsed = (datetime.now(UTC) - job["started_at"]).total_seconds()
    return min(99, max(0, int(elapsed / job["duration"] * 100)))


def serialize_job(job) -> dict:
    return {
        "job_id": str(job["job_id"]),
        "status": job["status"],
        "duration_seconds": job["duration"],
        "worker_id": job["worker_id"],
        "progress": calculate_progress(job),
        "error": job["error"],
        "created_at": job["created_at"].isoformat(),
        "started_at": (
            job["started_at"].isoformat() if job["started_at"] is not None else None
        ),
        "completed_at": (
            job["completed_at"].isoformat() if job["completed_at"] is not None else None
        ),
    }


def dashboard_state() -> dict:
    pool_workers = worker_pool.snapshot()
    running_jobs = demo_db.running_jobs_by_worker()

    workers = []
    for pool_worker in pool_workers:
        job = running_jobs.get(pool_worker["worker_id"])
        if not pool_worker["alive"]:
            status = "offline"
        elif pool_worker["lifecycle"] == "draining":
            status = "draining"
        elif job is not None:
            status = "running"
        else:
            status = "idle"

        workers.append(
            {
                **pool_worker,
                "status": status,
                "job": serialize_job(job) if job is not None else None,
            }
        )

    counts = demo_db.job_counts()
    return {
        "system": {
            "api": "online",
            "database": ("connected" if demo_db.database_is_ready() else "unavailable"),
            "cpu_count": worker_pool.max_workers,
            "worker_limit": worker_pool.max_workers,
            "configured_workers": worker_pool.desired_count,
            "live_workers": sum(worker["alive"] for worker in pool_workers),
            "jobs": counts,
        },
        "workers": workers,
        "jobs": [serialize_job(job) for job in demo_db.list_jobs(limit=100)],
    }


@app.errorhandler(psycopg.Error)
def handle_database_error(error):
    app.logger.exception("Database operation failed")
    return jsonify({"error": "Database is temporarily unavailable"}), 503


@app.get("/")
def index():
    return render_template(
        "index.html",
        default_duration=DEFAULT_DURATION_SECONDS,
    )


@app.post("/async-export")
def create_async_export_job():
    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    duration = payload.get("duration_seconds", DEFAULT_DURATION_SECONDS)
    if (
        isinstance(duration, bool)
        or not isinstance(duration, int)
        or not 1 <= duration <= MAX_DURATION_SECONDS
    ):
        return (
            jsonify(
                {
                    "error": (
                        "duration_seconds must be an integer between "
                        f"1 and {MAX_DURATION_SECONDS}"
                    )
                }
            ),
            400,
        )

    job = demo_db.create_job(duration)
    return jsonify(serialize_job(job)), 202


@app.get("/async-export/<job_id>/status")
def async_export_status(job_id: str):
    job = demo_db.get_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(serialize_job(job))


@app.get("/async-export/<job_id>/download")
def download_async_export(job_id: str):
    job = demo_db.get_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    if job["status"] == "error":
        return (
            jsonify(
                {
                    "job_id": job_id,
                    "status": job["status"],
                    "error": job["error"],
                }
            ),
            422,
        )

    if job["status"] != "completed":
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


@app.get("/demo/system")
def demo_system():
    return jsonify(dashboard_state()["system"])


@app.get("/demo/workers")
def demo_workers():
    return jsonify({"workers": dashboard_state()["workers"]})


@app.put("/demo/workers")
def update_demo_workers():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    count = payload.get("count")
    try:
        worker_pool.scale(count)
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify(
        {
            "configured_workers": worker_pool.desired_count,
            "worker_limit": worker_pool.max_workers,
            "workers": worker_pool.snapshot(),
        }
    )


@app.get("/demo/jobs")
def demo_jobs():
    status = request.args.get("status")
    try:
        jobs = demo_db.list_jobs(limit=100, status=status)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"jobs": [serialize_job(job) for job in jobs]})


@app.get("/demo/dashboard")
def demo_dashboard():
    return jsonify(dashboard_state())


if __name__ == "__main__":
    worker_pool.start()
    atexit.register(worker_pool.shutdown)
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
