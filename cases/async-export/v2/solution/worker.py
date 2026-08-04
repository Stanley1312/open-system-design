from multiprocessing import Process
import os
from enum import Enum
import time


class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


def worker(worker_id: int, process_job_cb, run_job_cb, update_job_cb) -> None:
    print(f"Start worker={worker_id} sucessfull")
    while True:
        job = process_job_cb()
        print(f"Worker {worker_id}: current job {job}")

        if job is None:
            time.sleep(1)
            continue
        try:
            result = run_job_cb(job)

            update_job_cb(
                {"job_id": job["job_id"], "status": Status.COMPLETED, "result": result}
            )

        except Exception as error:
            print(f"Error: {error}")
            update_job_cb(
                {
                    "job_id": job["job_id"],
                    "status": Status.ERROR,
                    "error": "Database error !",
                }
            )
