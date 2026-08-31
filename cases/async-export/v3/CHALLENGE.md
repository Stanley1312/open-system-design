# Async Export V3 Challenge

## Learning goal

Build a recoverable PostgreSQL worker queue. When a worker disappears during a
long-running export, another worker must safely reclaim the abandoned job and
resume after its last completed chunk.

## Requirements

- Preserve the V2 create, status, and download API behavior.
- Claim one pending job atomically with `FOR UPDATE SKIP LOCKED`.
- Assign a new lease token on every claim.
- Mark a claimed job as running and initialize its heartbeat timestamp.
- Renew the heartbeat while the job is being processed.
- Perform work in chunks and save a checkpoint only after a chunk completes.
- Calculate progress from the saved checkpoint.
- Reclaim a running job when its heartbeat becomes stale.
- Clear the expired lease and return the abandoned job to pending.
- Resume a reclaimed job after its last saved checkpoint.
- Fence heartbeat, checkpoint, completion, and error writes with the active
  lease token.
- A worker that has lost ownership must abandon its attempt instead of
  overwriting the new owner's state.

## Observable recovery scenario

1. Create a job long enough to observe several checkpoints.
2. Record the PID of the worker processing it.
3. Terminate that worker process abruptly.
4. Confirm the job remains running until its heartbeat expires.
5. Confirm the reaper changes it back to pending without clearing the
   checkpoint.
6. Confirm another worker claims it with a different lease and resumes from
   the next chunk.
7. Confirm the job eventually completes and progress never exceeds 100%.

## Failure boundaries

- Unknown job IDs return `404`.
- Invalid durations return `400`.
- A download before completion returns `409`.
- A permanently failed job returns its error response.
- A fenced database update that affects no row means the worker no longer owns
  that job.

## Out of scope

- Restarting crashed worker or reaper processes
- Detecting a live process whose current chunk is stuck
- Retrying ordinary application failures with attempt limits or backoff
- Object storage, multipart output, and presigned URLs
- Exactly-once external side effects
