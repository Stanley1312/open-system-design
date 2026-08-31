# Async Export V2 — PostgreSQL Worker Queue

V2 turns the in-memory simulation from V1 into a real PostgreSQL-backed job
queue consumed by multiple Python worker processes.

## Learning path

1. Read CHALLENGE.md.
2. Build the queue flow in starter/.
3. Compare your work with the owner implementation in solution/.
4. Run the interactive demo/ to watch jobs move through the queue.
5. Read docs/ for the transaction and worker-pool details.

## What changes from V1?

| V1                        | V2                                       |
| ------------------------- | ---------------------------------------- |
| In-memory job dictionary  | PostgreSQL jobs table                    |
| Simulated background work | Separate worker processes                |
| No competing consumers    | Multiple workers claim jobs concurrently |
| Process-local state       | Persisted job status and result          |
| No database locking       | FOR UPDATE SKIP LOCKED                   |

## Repository layout

    v2/
    ├── CHALLENGE.md
    ├── starter/       # Runnable learning scaffold
    ├── solution/      # Owner implementation, preserved as written
    ├── demo/          # Observable version with UI-only APIs
    ├── docs/          # Deeper design notes
    └── run_demo.sh    # Starts the demo database and application

## Run the interactive demo

From this directory:

    ./run_demo.sh

Open http://127.0.0.1:5000. The demo starts with two workers and lets you
scale the pool up to the CPU count visible to the application container.

The demo implementation mirrors the owner flow but is intentionally separate.
The files in solution/ are not imported or modified by the visualizer.
