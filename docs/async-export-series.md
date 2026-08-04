# Async Export Learning Series

The Async Export case evolves one implementation instead of introducing a large
production architecture all at once.

| Version | Storage               | Execution                 | Main lesson                                                        |
| ------- | --------------------- | ------------------------- | ------------------------------------------------------------------ |
| V1      | In-memory dictionary  | Simulated elapsed time    | Why a long export should become an asynchronous job                |
| V2      | PostgreSQL jobs table | Multiple worker processes | How consumers claim queued work safely with FOR UPDATE SKIP LOCKED |
| V3      | Planned               | Planned                   | Retry, heartbeat, reaper, lease, and recovery                      |

## V1

V1 compares a blocking export request with an asynchronous job API. It keeps
state in memory and simulates worker progress with elapsed time so the browser
interaction is easy to understand.

Its interactive UI lives directly inside the reference solution.

## V2

V2 replaces the in-memory dictionary with PostgreSQL and introduces real worker
processes. Multiple workers use transactions and row locking to claim different
pending jobs safely.

The owner solution is preserved as written. A separate interactive demo adds
worker IDs, observability APIs, pool scaling, and a live dashboard without
making those concerns part of the core challenge.

Continue with [Async Export V1](../cases/async-export/v1/) or
[Async Export V2](../cases/async-export/v2/).
