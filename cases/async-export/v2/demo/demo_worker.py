"""Worker loop for the interactive demo.

This follows ../solution/worker.py and adds worker identity plus a stop event
for graceful pool scaling.
"""

import time

from demo_db import claim_pending_job, complete_job, fail_job


def run_export(job):
    duration = job["duration"]
    if duration <= 0:
        raise ValueError("Job duration must be greater than zero")

    time.sleep(duration)
    return (
        "Async export completed.\n"
        f"Job ID: {job['job_id']}\n"
        f"Worker: {job['worker_id']}\n"
        f"Simulated duration: {duration} seconds.\n"
    )


def worker_loop(worker_id: int, stop_event) -> None:
    print(f"Worker {worker_id} started", flush=True)

    while not stop_event.is_set():
        job = claim_pending_job(worker_id)
        if job is None:
            stop_event.wait(0.5)
            continue

        print(f"Worker {worker_id} claimed job {job['job_id']}", flush=True)
        try:
            result = run_export(job)
            complete_job(job["job_id"], result)
            print(f"Worker {worker_id} completed job {job['job_id']}", flush=True)
        except Exception as error:  # noqa: BLE001 - persist all job failures
            fail_job(job["job_id"], str(error))
            print(f"Worker {worker_id} failed job {job['job_id']}: {error}", flush=True)

    print(f"Worker {worker_id} stopped", flush=True)
