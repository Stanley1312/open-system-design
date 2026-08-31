from multiprocessing import Process
import os
import time
import threading
from datetime import datetime
import uuid

from enums import Status


def reaper(reaper_name: str, restate_failed_jobs_cb, interval: int = 30) -> None:
    print(f"Start Reaper={reaper_name} sucessfull")
    next_run = time.monotonic()

    while True:
        restated_jobs = restate_failed_jobs_cb(interval)
        print(f"There are {len(restated_jobs)} dead jobs.")

        next_run += interval
        sleep_time = next_run - time.monotonic()
        if sleep_time > 0:
            time.sleep(sleep_time)


def worker(
    worker_id: int,
    add_heartbeat_cb,
    process_job_cb,
    run_job_cb,
    update_job_cb,
    interval: int = 10,
) -> None:
    print(f"Start worker={worker_id} - PID={os.getpid()} sucessfull")

    while True:
        job = None
        heartbeat_thread = None
        stop_heartbeat = threading.Event()
        lease_token = uuid.uuid4()

        try:
            job = process_job_cb(lease_token)

            if job is None:
                time.sleep(1)
                continue

            heartbeat_thread = threading.Thread(
                target=run_heartbeat,
                args=(
                    worker_id,
                    job,
                    lease_token,
                    add_heartbeat_cb,
                    stop_heartbeat,
                    interval,
                ),
            )

            heartbeat_thread.start()

            result = run_job_cb(os.getpid(), job, lease_token)

            stop_heartbeat.set()
            print("Stop heartbeat thread successfull !.")

            update_job_cb(
                {
                    "job_id": job["job_id"],
                    "status": Status.COMPLETED,
                    "result": result,
                    "lease_token": lease_token,
                }
            )

        except RuntimeError as ownership_error:
            print(f"RuntimeError: {ownership_error}")


        except Exception as error:
            print(f"Error: {error}")
            if job:
                update_job_cb(
                    {
                        "job_id": job["job_id"],
                        "status": Status.ERROR,
                        "error": "Database error !",
                        "lease_token": lease_token,
                    }
                )
        finally:
            stop_heartbeat.set()
            if heartbeat_thread is not None:
                heartbeat_thread.join()


def run_heartbeat(
    worker_id: int,
    job,
    lease_token: uuid.UUID,
    add_heartbeat_cb,
    stop_event: threading.Event,
    interval: int,
) -> None:
    while not stop_event.is_set():
        try:
            add_heartbeat_cb(job, lease_token)
            print(
                f"[{datetime.now():%H:%M:%S}] "
                f"Worker={worker_id} job={job['job_id']} heartbeat done!"
            )
        except Exception as error:
            print(f"Heartbeat stopped: {error}")
            return
        stop_event.wait(interval)
