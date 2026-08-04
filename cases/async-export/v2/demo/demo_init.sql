CREATE TABLE jobs (
    job_id UUID PRIMARY KEY,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('pending', 'running', 'completed', 'error')),
    duration INTEGER NOT NULL CHECK (duration BETWEEN 1 AND 120),
    worker_id INTEGER,
    result TEXT,
    error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX jobs_pending_queue_idx
    ON jobs (created_at)
    WHERE status = 'pending';
