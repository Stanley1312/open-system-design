# Async Export V3 — Reference Solution

This implementation runs a Flask API, two worker processes, and one reaper
process against PostgreSQL. Workers process a simulated export in one-second
chunks and persist a checkpoint after each completed chunk.

## Prerequisites

- Python 3.14 or the version declared in `.python-version`
- `uv`
- Docker for the local PostgreSQL container

Create a local `.env` from the case-level `.env.example` and provide the
PostgreSQL database, user, and password expected by `db.py` and `run_db.sh`.

## Start

From this directory:

```bash
uv sync
./run_db.sh
uv run python main.py
```

Create a job from another terminal:

```bash
curl -X POST http://127.0.0.1:5000/async-export \
  -H 'Content-Type: application/json' \
  -d '{"duration_seconds": 90}'
```

Use the returned ID with:

```bash
curl http://127.0.0.1:5000/async-export/JOB_ID/status
curl -OJ http://127.0.0.1:5000/async-export/JOB_ID/download
```

## Demonstrate recovery

Worker startup logs include their PIDs. While a long job is running, terminate
only its worker from another terminal:

```bash
kill -9 WORKER_PID
```

Do not kill the Flask parent or reaper. After the heartbeat expiry window, the
reaper returns the job to pending. The surviving worker claims it with a new
lease token and resumes after the stored checkpoint.

The parent process in this demo does not replace the killed worker. Production
deployments delegate worker-process replacement to a supervisor such as
Kubernetes, systemd, ECS, or a container restart policy.

## Stop the database

The helper currently creates a container named `async-export`. Stop and remove
that development container using your normal Docker workflow before rerunning
the initialization from scratch.
