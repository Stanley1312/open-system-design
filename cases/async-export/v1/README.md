# Async Export V1 — System Design Lab

Version 1 compares a blocking synchronous file export with a polling-based
asynchronous export. Database queries and worker execution are intentionally
simulated with elapsed time so the HTTP interaction is easy to observe.

## Choose your path

- [Try the challenge](CHALLENGE.md), then work inside [`starter/`](starter/).
- Compare your implementation with the reference code in
  [`solution/`](solution/).
- [Read the V1 design note](docs/in-memory-async-export.md) for the decisions
  and intentional shortcuts in this version.
- [Read the case-wide architecture note](../docs/async_large_file_export_api_design_en.md)
  for the production-oriented system that later versions build toward.

## Repository layout

```text
v1/
├── README.md       # Case overview
├── CHALLENGE.md    # Requirements and hints
├── starter/        # Minimal runnable scaffold
├── solution/       # Reference implementation
└── docs/           # V1-specific design notes
```

## Run the reference solution

```bash
cd solution
uv sync
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
