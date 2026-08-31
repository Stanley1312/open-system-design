# V1 Design Note — In-Memory Async Export

V1 isolates the first architectural change in the case: an export should not
keep one HTTP request open for the entire processing time.

## Synchronous baseline

The synchronous endpoint performs the simulated export before returning the
response. This keeps the flow simple, but the client receives no progress and
the request may time out when real exports become slow.

```text
Client ── POST /sync-export ──▶ Server processes export ──▶ File response
          one HTTP request remains open for the whole duration
```

## V1 asynchronous flow

V1 separates job creation, status checks, and download into short requests:

```text
Client ── POST /async-export ─────────────▶ create in-memory job
Client ◀─ 202 Accepted + job_id ──────────

Client ── GET /async-export/<id>/status ──▶ calculate simulated progress
Client ◀─ status + progress ───────────────

Client ── GET /async-export/<id>/download ▶ return the completed result
```

The browser polls the status endpoint until the job completes. Each request is
short, so the client can show progress without holding the original export
request open.

## Intentional simulation

There is no background worker in V1. A job stores its start time and requested
duration in a process-local Python dictionary. On every status request, the
application derives progress from elapsed wall-clock time:

```text
progress = elapsed time / requested duration × 100
```

This is enough to teach the asynchronous HTTP contract before introducing the
database and worker coordination used in V2.

## Boundaries

- A process restart loses every job.
- Multiple application processes do not share job state.
- Progress represents elapsed time, not completed work.
- No worker actually produces a file in the background.
- Authentication, ownership, retries, and expiration are out of scope.

These are learning boundaries, not production recommendations. See the
[case-wide architecture note](../../docs/async_large_file_export_api_design_en.md)
for the later persistence, worker, recovery, checkpoint, and object-storage
steps.
