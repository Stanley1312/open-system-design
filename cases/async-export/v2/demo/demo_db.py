"""Database operations for the interactive demo.

The flow mirrors ../solution/db.py. The extra worker_id and list operations
exist only so the dashboard can visualize queue ownership.
"""

import os
import uuid

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://async_export:async_export@localhost:5432/async_export",
)

VALID_STATUSES = {"pending", "running", "completed", "error"}


def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def create_job(duration: int):
    job_id = str(uuid.uuid4())
    with get_connection() as connection:
        return connection.execute(
            """
            INSERT INTO jobs (job_id, status, duration)
            VALUES (%s, 'pending', %s)
            RETURNING *
            """,
            (job_id, duration),
        ).fetchone()


def claim_pending_job(worker_id: int):
    """Claim one job without waiting for rows locked by other workers."""
    with get_connection() as connection:
        return connection.execute(
            """
            WITH next_job AS (
                SELECT job_id
                FROM jobs
                WHERE status = 'pending'
                ORDER BY created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE jobs
            SET status = 'running',
                worker_id = %s,
                started_at = NOW(),
                updated_at = NOW()
            FROM next_job
            WHERE jobs.job_id = next_job.job_id
            RETURNING jobs.*
            """,
            (worker_id,),
        ).fetchone()


def complete_job(job_id, result: str):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE jobs
            SET status = 'completed',
                result = %s,
                error = NULL,
                completed_at = NOW(),
                updated_at = NOW()
            WHERE job_id = %s
            """,
            (result, job_id),
        )


def fail_job(job_id, error: str):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE jobs
            SET status = 'error',
                result = NULL,
                error = %s,
                completed_at = NOW(),
                updated_at = NOW()
            WHERE job_id = %s
            """,
            (error, job_id),
        )


def get_job(job_id: str):
    try:
        normalized_id = str(uuid.UUID(job_id))
    except ValueError:
        return None

    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM jobs WHERE job_id = %s",
            (normalized_id,),
        ).fetchone()


def list_jobs(limit: int = 100, status: str | None = None):
    if status is not None and status not in VALID_STATUSES:
        raise ValueError("Unknown job status")

    query = "SELECT * FROM jobs"
    parameters = []

    if status is not None:
        query += " WHERE status = %s"
        parameters.append(status)

    query += " ORDER BY created_at DESC LIMIT %s"
    parameters.append(limit)

    with get_connection() as connection:
        return connection.execute(query, parameters).fetchall()


def job_counts():
    counts = {status: 0 for status in VALID_STATUSES}
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT status, COUNT(*) AS count FROM jobs GROUP BY status"
        ).fetchall()

    for row in rows:
        counts[row["status"]] = row["count"]
    return counts


def running_jobs_by_worker():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM jobs
            WHERE status = 'running' AND worker_id IS NOT NULL
            ORDER BY started_at
            """
        ).fetchall()
    return {row["worker_id"]: row for row in rows}


def database_is_ready() -> bool:
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False
