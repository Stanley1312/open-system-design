"""Small, explicit process manager used only by the interactive demo."""

import multiprocessing
import os
import threading
from dataclasses import dataclass

from demo_worker import worker_loop


@dataclass
class WorkerHandle:
    worker_id: int
    process: multiprocessing.Process
    stop_event: object
    lifecycle: str = "active"


class WorkerPool:
    def __init__(self, initial_workers: int = 2):
        self.max_workers = os.cpu_count() or 1
        self.initial_workers = max(1, min(initial_workers, self.max_workers))
        self.desired_count = 0
        self._next_worker_id = 0
        self._workers: dict[int, WorkerHandle] = {}
        self._lock = threading.RLock()
        self._context = multiprocessing.get_context("spawn")

    def start(self) -> None:
        self.scale(self.initial_workers)

    def scale(self, count: int) -> None:
        if isinstance(count, bool) or not isinstance(count, int):
            raise TypeError("Worker count must be an integer")
        if not 1 <= count <= self.max_workers:
            raise ValueError(f"Worker count must be between 1 and {self.max_workers}")

        with self._lock:
            self._reap_stopped_workers()
            self.desired_count = count
            active_workers = [
                handle
                for handle in self._workers.values()
                if handle.lifecycle == "active" and handle.process.is_alive()
            ]

            if count > len(active_workers):
                for _ in range(count - len(active_workers)):
                    self._start_one_worker()
                return

            workers_to_stop = len(active_workers) - count
            for handle in sorted(
                active_workers,
                key=lambda item: item.worker_id,
                reverse=True,
            )[:workers_to_stop]:
                handle.lifecycle = "draining"
                handle.stop_event.set()

    def snapshot(self) -> list[dict]:
        with self._lock:
            self._reap_stopped_workers()
            return [
                {
                    "worker_id": handle.worker_id,
                    "pid": handle.process.pid,
                    "lifecycle": handle.lifecycle,
                    "alive": handle.process.is_alive(),
                }
                for handle in sorted(
                    self._workers.values(),
                    key=lambda item: item.worker_id,
                )
            ]

    def shutdown(self) -> None:
        with self._lock:
            handles = list(self._workers.values())
            for handle in handles:
                handle.lifecycle = "draining"
                handle.stop_event.set()

        for handle in handles:
            handle.process.join(timeout=3)
            if handle.process.is_alive():
                handle.process.terminate()
                handle.process.join(timeout=1)

    def _start_one_worker(self) -> None:
        worker_id = self._next_worker_id
        self._next_worker_id += 1

        stop_event = self._context.Event()
        process = self._context.Process(
            target=worker_loop,
            args=(worker_id, stop_event),
            name=f"demo-worker-{worker_id}",
            daemon=True,
        )
        process.start()
        self._workers[worker_id] = WorkerHandle(
            worker_id=worker_id,
            process=process,
            stop_event=stop_event,
        )

    def _reap_stopped_workers(self) -> None:
        stopped_ids = [
            worker_id
            for worker_id, handle in self._workers.items()
            if not handle.process.is_alive()
        ]
        for worker_id in stopped_ids:
            self._workers[worker_id].process.join(timeout=0)
            del self._workers[worker_id]
