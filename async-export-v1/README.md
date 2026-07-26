# Async Export — System Design Lab

Version 1 compares a blocking synchronous file export with a polling-based
asynchronous export. Database queries and worker execution are intentionally
simulated with elapsed time so the HTTP interaction is easy to observe.

## Choose your path

- [Try the challenge](CHALLENGE.md) — requirements, milestones, hints, and
  self-review questions without implementation code.
- [Read the design note](async_large_file_export_api_design_en.md) — the
  production-oriented architecture behind this simplified case.
- Explore the remaining files for the V1 reference solution.

## Run locally

```bash
uv run python main.py
```

Open <http://127.0.0.1:5000>.

For both demos, the client chooses a simulation duration between 1 and 120
seconds. The defaults are 10 seconds for sync and 20 seconds for async. The
async client automatically chooses a polling interval between 1 and 10 seconds
based on the selected duration.

## V1 limitations

- Jobs are stored in an in-memory dictionary and are lost on server restart.
- Elapsed time simulates a worker; there is no real task queue yet.
- Progress is estimated from elapsed time, not from committed database chunks.
- There is no authentication, ownership check, retry, or file expiration yet.
