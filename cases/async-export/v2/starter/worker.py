"""Worker scaffold for the Async Export V2 challenge."""

import time


def worker(worker_id: int, process_job_cb, run_job_cb, update_job_cb) -> None:
    while True:
        job = process_job_cb()
        if job is None:
            time.sleep(1)
            continue

        # TODO: run the job and persist completed/error status.
        raise NotImplementedError
