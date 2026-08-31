# Challenge — Build an Async Export API

## Goal

The starter demonstrates the problem: a synchronous export keeps one HTTP
request open until all work is finished.

Your task is to build the core asynchronous backend. A client should be able to
create an export job, check its progress, and download the result when ready.
You do **not** need to build or change the UI.

## Start with the Problem

```bash
cd starter
uv sync
uv run python main.py
```

Open <http://127.0.0.1:5000> and run the synchronous export once. Notice that
the client receives no response or progress while the server is working.

## Build Three Endpoints

### 1. Create a job

```http
POST /async-export
Content-Type: application/json

{ "duration_seconds": 20 }
```

Create an in-memory job and return immediately with `202 Accepted`:

```json
{
  "job_id": "7de89ca3-71f3-4634-b082-5c71b22b3347",
  "status": "running",
  "duration_seconds": 20
}
```

Accept durations from 1 to 120 seconds. Reject invalid input with `400`.

### 2. Read job status

```http
GET /async-export/<job_id>/status
```

Return the job's status and progress:

```json
{
  "job_id": "7de89ca3-71f3-4634-b082-5c71b22b3347",
  "status": "running",
  "progress": 40
}
```

For this simulation, calculate progress from elapsed time:

```text
elapsed time / requested duration × 100
```

Progress must stay between `0` and `100`. At `100`, return `completed`. Return
`404` for an unknown job.

### 3. Download the result

```http
GET /async-export/<job_id>/download
```

Return a text file attachment when the job is complete. Return `404` when the
job does not exist and `409 Conflict` while it is still running.

## Keep V1 Small

- Store jobs in a Python dictionary.
- Use elapsed time to simulate background progress.
- Do not add a database, task queue, worker, Redis, or cloud service.
- Keep the complete request flow easy to trace.

These shortcuts are intentional. Later versions will address persistence,
workers, retries, and object storage.

## Done When

- Creating a job returns before its duration has elapsed.
- The returned `job_id` works in the status and download URLs.
- Progress never exceeds `100`.
- Invalid input and unknown jobs return the expected status codes.
- Download is rejected until the job is complete.

When these checks pass, compare your code with `solution/`, then read the
[V1 design note](docs/in-memory-async-export.md) to review this version's
trade-offs. The [case-wide architecture note](../docs/async_large_file_export_api_design_en.md)
shows what must change in a production system.
