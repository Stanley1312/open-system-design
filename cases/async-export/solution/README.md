# Async Export V1 — Reference Solution

This implementation compares:

- A synchronous request that remains open during simulated processing.
- An asynchronous job created immediately and monitored through client polling.

## Run

```bash
uv sync
uv run python main.py
```

Open <http://127.0.0.1:5000>.

Both sides let the client choose a simulation duration between 1 and 120
seconds. The async client adjusts its polling interval to keep short demos
responsive.

## Important limitations

This is intentionally a V1 learning implementation:

- Jobs exist only in the Flask process memory.
- Elapsed time simulates worker progress.
- No actual task queue or separate worker is used.
- Generated files are kept in memory.
- Authentication, ownership, retries, and expiration are not implemented.

Read the [case design note](../docs/async_large_file_export_api_design_en.md) to
understand how a production-oriented version addresses these limitations.
