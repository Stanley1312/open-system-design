# Async Export V3 Design Notes

## Ownership model

`status = running` alone cannot identify the current owner of a job. Every
claim therefore creates a new UUID lease token. All writes performed by that
worker include the job ID, running status, and lease token in their `WHERE`
clause.

If the update affects zero rows, the attempt has lost ownership and must stop
writing. This protects the database if an old worker resumes after the reaper
has reassigned its job.

## Heartbeat and reaper

The heartbeat stored on a job is a renewable job lease, not a complete worker
health check. While processing a job, a small thread periodically updates
`last_heartbeat_at`. The thread uses an interruptible event wait and is joined
before the worker begins its next polling iteration.

The reaper periodically performs one conditional update:

```text
running job + expired heartbeat → pending job + cleared lease
```

Combining detection and reclaim in one database statement prevents a stale
read followed by an unconditional update. A conditional PostgreSQL update also
serializes concurrent attempts to change the same row, so the demo does not
need a separate `SELECT ... SKIP LOCKED` in its reaper.

## Checkpoint semantics

`checkpoint_offset = N` means that chunk N completed safely. Work is performed
before the checkpoint is persisted. A new owner therefore resumes at N + 1.
The status endpoint derives progress from the checkpoint rather than elapsed
wall-clock time.

The simulation updates only a database offset. A real export would need to
coordinate checkpoint persistence with durable output so a crash cannot leave
the output and checkpoint inconsistent.

## Retry semantics

V3 demonstrates retry after infrastructure failure:

```text
worker attempt disappears
→ lease expires
→ reaper returns job to pending
→ another attempt resumes it
```

An exception raised during normal job processing is not retried in this demo;
it moves the job to `error`. Retry limits, backoff, jitter, and dead-letter
handling would be a separate extension.

## Process supervision boundary

The reaper recovers jobs, not worker processes. The heartbeat attached to a job
does not prove that every part of the worker is healthy, and it cannot restart
the process that emits it.

Production deployments use an external supervisor to maintain worker and
reaper processes. Kubernetes, systemd, ECS, Nomad, or container restart
policies are common examples. Detecting a process that is alive while its job
thread is stuck requires a separate progress watchdog and is outside V3.

## Intentional limitations

- One parent process starts Flask, two workers, and one reaper.
- A killed worker is not replaced by the parent.
- Heartbeat failures are logged; ownership loss is discovered by fenced writes.
- A chunk is simulated with `sleep(1)`.
- Results are stored as text in PostgreSQL rather than object storage.
- There is no retry budget for normal application errors.
- There is no authentication, authorization, expiration, or cleanup policy.
