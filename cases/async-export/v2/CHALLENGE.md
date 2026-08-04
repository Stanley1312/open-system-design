# Async Export V2 Challenge

Implement a PostgreSQL-backed asynchronous export queue that can be consumed
safely by multiple worker processes.

## Requirements

- POST /async-export validates a duration and returns 202 with a new job ID.
- A new job is persisted with the pending status.
- Multiple workers may poll the same queue concurrently.
- A pending job must be claimed by at most one worker.
- Claim work inside a transaction with FOR UPDATE SKIP LOCKED.
- A claimed job becomes running and receives a start timestamp.
- Successful work becomes completed and stores a downloadable result.
- Failed work becomes error and stores a human-readable error message.
- Unknown job IDs return 404.
- A premature download returns 409 Conflict.
- Progress never exceeds 100 percent.

## Suggested order

1. Create the database schema.
2. Implement job creation and lookup.
3. Implement transactional job claiming.
4. Run one worker process.
5. Add multiple workers and verify a job is never processed twice.
6. Add status polling and download behavior.

The dashboard under demo/ is a visualization aid. Recreating it is not part of
the challenge.
