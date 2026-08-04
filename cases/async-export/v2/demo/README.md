# Async Export V2 — Interactive Demo

This implementation follows the same PostgreSQL queue and multiprocessing flow
as the owner implementation in ../solution. It adds observability endpoints,
worker identity, and graceful pool scaling only for the interactive UI.

It is intentionally explicit: Flask, Psycopg, multiprocessing, HTML, CSS, and
plain browser JavaScript. There is no ORM, task framework, or WebSocket layer.

## Run

From the V2 directory:

    ./run_demo.sh

Open http://127.0.0.1:5000.

Try creating more jobs than workers. Pending jobs remain in PostgreSQL until a
worker becomes available. Increase the pool and watch multiple workers claim
different rows through FOR UPDATE SKIP LOCKED.

The PostgreSQL service uses temporary storage, so every full Compose restart
starts with an empty queue.
