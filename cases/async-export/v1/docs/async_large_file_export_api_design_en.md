# Note: Designing an API for Exporting Large Files — Asynchronous Model

> Source: summarized from the "Dem IT." reel — a five-step approach to building an export API that avoids timeouts and prevents data loss when a worker crashes midway.

---

## The Core Problem

Previously, a single `export` API received the request, processed the export while the client waited, and returned the file when processing finished.

**Drawback:** if the file is large and takes a long time to process, the client may **time out**, causing the result to be lost.

**Overall solution:** split the process into two APIs and use a background worker system for asynchronous processing.

```text
Client                          Server
  |  POST /api/export               |
  |--------------------------------->|  Create a "job" row with pending status
  |  <-- 202 Accepted + job_id ------|
  |                                  |
  |  GET /status?job_id=xxx          |
  |--------------------------------->|  Worker is processing in the background
  |  <-- { progress: 45% } ----------|
  |                                  |
  |  GET /status?job_id=xxx (repeat) |
  |--------------------------------->|
  |  <-- { status: done, url } ------|
```

---

## Step 1/5 — Split One API into Two Asynchronous APIs

- **`POST /api/export`**: only inserts a job record into the `jobs` table with the status `pending`. It immediately returns **202 Accepted** together with a `job_id`. The response is fast, so there is no risk of a request timeout.
- **`GET /status`**: the client uses the `job_id` to periodically check the job status through polling. Once the job is complete, the API returns a download link.

> Where do multiple jobs in the `jobs` table come from? Primarily from **multiple users starting exports at the same time**. Jobs can also come from one user exporting different report types, retries after worker failures as described in Step 3, or automatically scheduled jobs such as cron jobs.

---

## Step 2/5 — Process Jobs with a Worker Pool

- Multiple **workers** run in parallel. Each worker is a background process that is independent of the API. Every worker continuously loops: fetch one `pending` job, process it, and save the result.
- **A single job is processed by exactly one worker from start to finish.** A job is not divided among multiple workers. This is different from parallel-processing or MapReduce models.
- The main challenge is preventing two workers from picking up the same job.

**Solution:** use `SELECT ... FOR UPDATE SKIP LOCKED`, supported by MySQL 8+ and PostgreSQL.

```sql
BEGIN;

SELECT *
FROM jobs
WHERE status = 'pending'
ORDER BY created_at
LIMIT 1
FOR UPDATE SKIP LOCKED;

-- Update the job status to 'processing', then commit immediately.
```

- `FOR UPDATE`: locks the selected row.
- `SKIP LOCKED`: if another worker has already locked a row, the current worker **skips it instead of waiting** and moves to the next unlocked row.

```text
Worker 1 ──► Job #101 (locked and being processed)
Worker 2 ──► Job #102 (picked immediately after skipping #101)
Worker 3 ──► Job #103 (still pending and waiting to be picked)
```

As a result, no two workers process the same job, and workers do not have to wait for one another.

---

## Step 3/5 — Reaper Monitor for Detection and Recovery

- A worker may **crash unexpectedly** during processing because of an out-of-memory error, `kill -9`, server scale-down, or another failure.
- Without monitoring, the job remains stuck in the `processing` state forever because the system does not know that the worker has died.

**Solution:**

- While processing a job, each worker must continuously send a **heartbeat** indicating that it is still alive.
- A separate process called the **Reaper** periodically scans for jobs whose status is `processing` but whose heartbeat has expired. For example, if no heartbeat has been received for more than 60 seconds, the Reaper considers the worker dead and either moves the job back to `pending` so another worker can retry it or marks the job as `failed`.

```text
Worker #2 processes a job → OOM / kill -9 → heartbeat stops
                                               │
                          Reaper detects heartbeat older than 60 seconds
                                               │
                             Move the job back to pending for retry
```

---

## Step 4/5 — Save a Checkpoint for Each Chunk

**Problem:** suppose a worker is exporting a large file containing 3,000 rows and crashes midway. Does the next worker have to restart the entire job from the beginning? Without checkpoints, **yes**, which wastes a significant amount of work.

**Solution:** the worker divides its own work into smaller **chunks**, for example 1,000 rows per chunk. Each chunk is processed within **one transaction**.

```sql
BEGIN;

-- Process rows 1001–2000 and write them to the file.
UPDATE jobs
SET checkpoint_offset = 2000
WHERE id = 101;

COMMIT;
```

```text
Chunk 1, rows 1–1000:       ✓ Committed
Chunk 2, rows 1001–2000:    ✓ Committed
Chunk 3, rows 2001–3000:    Currently processing and not yet committed

checkpoint_offset = 2000
progress = 2000 / total rows × 100%
```

- If the worker crashes **during** Chunk 3, the transaction has not been committed, so Chunk 3 is rolled back cleanly and is treated as if it never happened. The `checkpoint_offset` remains `2000`, which was committed after Chunk 2.
- A new worker can pick up the job, read `checkpoint_offset = 2000`, and continue from row 2001 instead of restarting from the beginning. This avoids both repeated work and duplicate output.
- This is also why `GET /status` can return a **real progress percentage** based on the number of rows safely committed in the database rather than an estimate.

> Note: this does **not** mean that multiple workers are sharing one job. Chunking is performed internally by **one worker** so that it has safe resume points.

---

## Step 5/5 — Object Storage and Presigned URLs

- The generated file should **not be stored on the processing server**. Instead, it should be uploaded to object storage such as Amazon S3 or MinIO.
- The `jobs` table stores only the file **key**, or object path, rather than the actual file.
- When the client checks the status and the job is complete, the API returns a **time-limited presigned URL**, for example one that expires after 15 minutes.
- The system should not return a permanent public URL because it may be guessed, accessed without authorization, or expose one user's data to another user.

```text
Worker finishes processing
          │
          ▼
Upload file to s3://bucket/exports/2026/report.csv
          │
          ▼
Generate a presigned URL that expires after 15 minutes
          │
          ▼
GET /status returns the URL for the client to download the file
```

---

## Frequently Asked Questions

### Does the client need to keep fetching the status through polling? Is there a better approach?

Simple polling with exponential backoff, such as 2 seconds, then 4 seconds, then 8 seconds, is still widely used because it is easy to implement and works well for short- or medium-duration jobs.

Other options include:

- **Long polling**: the server keeps the request open until an update is available.
- **Server-Sent Events, or SSE**: the server pushes progress updates over a persistent connection.
- **WebSocket**: supports bidirectional, real-time communication.
- **Webhook**: the server calls the client back when the job is complete. This is suitable when the client is also a server.

### Are there multiple jobs mainly because there are multiple users?

Mostly yes. However, jobs can also be created when one user exports multiple report types, when a failed job is retried, or when the system automatically creates scheduled jobs through cron.

### Can multiple workers process one job in parallel, similar to MapReduce?

**No.** In this model, each job is processed completely by one worker.

Multiple workers run in parallel, but each worker handles a different job. The chunking described in Step 4 is only an internal mechanism used by one worker to create safe resume points. It does not distribute the chunks to other workers.

To process a single job with multiple workers, the system would require a more complex architecture, such as Spark, Hadoop, or a custom subtask-distribution layer.

---

## Overall System Architecture

```text
                    ┌─────────────────────────┐
   Client  ───POST──▶ API: Create a job       │
                    │ jobs table: pending     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ Worker Pool             │
                    │ SELECT FOR UPDATE       │
                    │ SKIP LOCKED             │
                    └────────────┬────────────┘
                                 │ Process in chunks
                                 │ Update checkpoint_offset
                    ┌────────────▼────────────┐
                    │ Reaper Monitor          │──▶ Dead job? Move it back to pending
                    │ Check worker heartbeat  │
                    └────────────┬────────────┘
                                 │ Complete
                    ┌────────────▼────────────┐
                    │ Upload to S3 or MinIO   │
                    │ Generate presigned URL  │
                    └────────────┬────────────┘
                                 │
   Client  ◀──GET /status────────┘  Progress percentage or download URL
```
