"""Database scaffold for the Async Export V2 challenge."""

import os

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://async_export:async_export@localhost:5432/async_export",
)


def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def process_job():
    """Claim and return one pending job.

    TODO: perform the selection and status update in one transaction. Multiple
    worker processes must not receive the same job.
    """
    raise NotImplementedError
