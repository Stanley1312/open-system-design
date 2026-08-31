import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv
import uuid

from enums import Status

load_dotenv()


db_name = os.getenv("POSTGRES_DB")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@localhost:5432/{db_name}"


def get_connection() -> Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def process_job(lease_token: uuid.UUID):
    with get_connection() as connection:
        pending_job = connection.execute(
            f"""
            WITH selected_job as (
             SELECT job_id FROM jobs
                WHERE status = %s
                order by created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
               UPDATE jobs
                    SET status = %s,
                    started_at = NOW(),
                    last_heartbeat_at = NOW(),
                    updated_at = NOW(),
                    lease_token = %s
                FROM selected_job
                WHERE jobs.job_id = selected_job.job_id
                RETURNING jobs.*;
                """,
            (Status.PENDING, Status.RUNNING, lease_token),
        ).fetchone()
        return pending_job


def get_job(connection, job_id):
    job = connection.execute(
        f"""
        SELECT * FROM jobs
            WHERE job_id = %s
                LIMIT 1;
    """,
        (job_id,),
    ).fetchone()
    return job


def update_job(job):
    result = job.get("result")
    error = job.get("error")
    lease_token = job.get("lease_token")

    with get_connection() as connection:
        cursor = connection.execute(
            f"""
             UPDATE jobs
                SET status = %s,
                    result = %s,
                    error = %s,
                    lease_token = NULL,
                    last_heartbeat_at = NOW(),
                    updated_at = NOW()
            WHERE job_id = %s
            AND status = %s
            AND lease_token = %s;
        """,
            (job["status"], result, error, job["job_id"], Status.RUNNING, lease_token),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("Worker no longer owns this job")


def restate_failed_job(limit_interval: int):
    with get_connection() as connection:
        return connection.execute(
            f"""
             UPDATE jobs
                SET status = %s,
                    lease_token = NULL,
                    updated_at = NOW()
            WHERE last_heartbeat_at <= CURRENT_TIMESTAMP - (%s * INTERVAL '1 second')
            AND status = %s
            RETURNING job_id;
        """,
            (
                Status.PENDING,
                limit_interval,
                Status.RUNNING,
            ),
        ).fetchall()


def add_heartbeat(job, lease_token: uuid.UUID):
    with get_connection() as connection:
        cursor = connection.execute(
            f"""
             UPDATE jobs
                SET
                    last_heartbeat_at = NOW(),
                    updated_at = NOW()
            WHERE job_id = %s and status = %s and lease_token = %s;
        """,
            (job["job_id"], Status.RUNNING, lease_token),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("Worker no longer owns this job")


def update_job_checkpoint(job, checkpoint: int, lease_token: uuid.UUID) -> None:
    with get_connection() as connection:
        cursor = connection.execute(
            f"""
                UPDATE jobs
                SET checkpoint_offset = %s,
                    updated_at = NOW()
            WHERE job_id = %s
                AND status = %s
                AND lease_token = %s;
        """,
            (checkpoint, job["job_id"], Status.RUNNING, lease_token),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("Worker no longer owns this job")
