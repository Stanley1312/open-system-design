import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()


db_name = os.getenv("POSTGRES_DB")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@localhost:5432/{db_name}"


class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


def get_connection() -> Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def process_job():
    with get_connection() as connection:
        pending_job = connection.execute(
            f"""
            SELECT * FROM jobs
                WHERE status = %s 
                order by created_at 
                LIMIT 1
                FOR UPDATE SKIP LOCKED;
        """,
            (Status.PENDING,),
        ).fetchone()
        if pending_job:
            connection.execute(
                f"""
                UPDATE jobs
                    SET status = %s,
                        started_at = NOW()
                WHERE job_id = %s;
            """,
                (Status.RUNNING, pending_job["job_id"]),
            )
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
    with get_connection() as connection:
        connection.execute(
            f"""
             UPDATE jobs
                SET status = %s,
                    result = %s,
                    error = %s,
                    updated_at = NOW()
            WHERE job_id = %s;
        """,
            (job["status"], result, error, job["job_id"]),
        )
