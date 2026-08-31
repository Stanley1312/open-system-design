# Async Export V3 — Starter

Build on the V2 PostgreSQL worker queue so an abandoned job can be reclaimed
and resumed safely.

Start with the requirements in `../CHALLENGE.md`. The central invariants are:

- only the current lease owner may write job state;
- a heartbeat expires when an attempt disappears;
- the reaper makes an abandoned job claimable again;
- a checkpoint represents work that has already completed safely.

Suggested implementation order:

1. Extend the jobs schema with heartbeat, lease, and checkpoint fields.
2. Assign a fresh lease during the atomic claim.
3. Fence all worker writes with that lease.
4. Add the heartbeat lifecycle.
5. Add the atomic reaper update.
6. Process chunks and resume from the checkpoint.
7. Derive status progress from committed checkpoints.

## Run

Use the same PostgreSQL and `uv` workflow as V2 after replacing the starter
placeholder with your implementation.
