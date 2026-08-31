CREATE TABLE jobs (
    job_id UUID PRIMARY KEY,
    status VARCHAR(100) NOT NULL,
    duration INTEGER DEFAULT 10,
    checkpoint_offset INTEGER,
    result TEXT,
    error TEXT,
    last_heartbeat_at TIMESTAMPTZ,
    lease_token UUID,
    started_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
