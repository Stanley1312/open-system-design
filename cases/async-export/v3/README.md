# Async Export V3 — Recovery and Resumable Work

V3 extends the PostgreSQL worker queue from V2 with recovery for a worker that
dies while processing a job. It introduces renewable job leases, heartbeat
timestamps, a reaper process, fencing tokens, and durable checkpoints.

## Learning path

1. Read `CHALLENGE.md` and identify why a `running` job may become abandoned.
2. Extend the scaffold in `starter/`.
3. Compare the result with `solution/`.
4. Kill a worker during a job and observe recovery from its checkpoint.
5. Read `docs/README.md` for the ownership and failure model.

## What changes from V2?

| V2 | V3 |
| --- | --- |
| A running job can remain stuck forever | Expired heartbeats are reclaimed |
| Job ownership is represented only by status | Every claim receives a lease token |
| A restarted job begins from the start | A restarted job resumes from a checkpoint |
| Progress is estimated from elapsed time | Progress comes from committed work |

## Recovery flow

```text
worker A claims job with lease A
        ↓
worker A processes chunks and renews its heartbeat
        ↓ worker A dies
reaper changes the stale job from running to pending
        ↓
worker B claims it with lease B
        ↓
worker B resumes after the last committed checkpoint
```

The lease token prevents Worker A from writing if it later resumes after the
job has already been assigned to Worker B.

## Scope

In this version, retry means recovery of an abandoned worker attempt. Ordinary
application errors become `error` immediately; retry counts, exponential
backoff, dead-letter queues, worker-process supervision, and stuck-job
detection are intentionally out of scope.

The implementation simulates one chunk with one second of work. It stores a
text result in PostgreSQL so the recovery mechanics remain easy to follow.
