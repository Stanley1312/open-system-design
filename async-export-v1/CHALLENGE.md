# Challenge — Build Async File Export V1

## Goal

Build a small application that demonstrates the difference between synchronous
and asynchronous file export.

This version intentionally uses simulated processing time and in-memory storage.
You do not need a real database, task queue, background worker, or object
storage yet.

## What you will learn

- Why long-running synchronous HTTP requests are problematic.
- How to model long-running work as a job.
- How a client polls job status.
- How to represent progress.
- How to download a result after processing completes.
- How HTTP methods and status codes describe an asynchronous workflow.

## Requirements

### 1. Synchronous export

Implement:

```http
GET /sync-export?time=10
```

Expected behavior:

1. Read a simulation duration from the query parameter.
2. Wait for that duration to simulate a slow database query.
3. Return a text file as an attachment.
4. Reject invalid durations.

The UI should contain:

- A duration input.
- A download button.
- A counter showing how long the request has been waiting.

### 2. Create an asynchronous export job

Implement:

```http
POST /async-export
Content-Type: application/json

{
  "duration_seconds": 20
}
```

Example response:

```json
{
  "job_id": "7de89ca3-71f3-4634-b082-5c71b22b3347",
  "status": "running",
  "duration_seconds": 20
}
```

The endpoint should return immediately instead of waiting for the export to
finish.

For V1, jobs may be stored in a Python dictionary.

### 3. Read job status

Implement:

```http
GET /async-export/<job_id>/status
```

Example response:

```json
{
  "job_id": "7de89ca3-71f3-4634-b082-5c71b22b3347",
  "status": "running",
  "progress": 40
}
```

Requirements:

- Progress must be between `0` and `100`.
- A completed job must return `status: "completed"`.
- An unknown job must return `404 Not Found`.

For this simulation, progress can be calculated from elapsed time:

```text
elapsed time / requested duration × 100
```

### 4. Download the asynchronous result

Implement:

```http
GET /async-export/<job_id>/download
```

Expected behavior:

- Return a file attachment when the job is complete.
- Return an error if the job does not exist.
- Return an appropriate non-success status if the job is still running.

### 5. Build the comparison UI

Create one page divided into two sections:

- Sync export on the left.
- Async export on the right.

The async section should:

1. Let the user choose a simulation duration.
2. Create an export job.
3. Poll the status endpoint.
4. Update a progress bar using the server response.
5. Automatically download the file at `100%`.

## Constraints

- Accepted simulation duration: 1–120 seconds.
- Do not use Celery, Redis, RabbitMQ, Kafka, or a cloud service in V1.
- Do not fake progress only in CSS; the displayed progress must come from the
  status API.
- Keep the code small enough that the complete HTTP flow is easy to follow.

## Suggested implementation order

1. Make the synchronous endpoint return a file.
2. Add its duration input and counter.
3. Create an in-memory async job.
4. Implement the status calculation.
5. Implement async download.
6. Add client polling.
7. Add validation and error states.

## Hints

<details>
<summary>Choosing an identifier</summary>

`uuid.uuid4()` creates a UUID object. Consider which representation should be
used consistently in dictionary keys, URLs, and JSON.

</details>

<details>
<summary>Representing status</summary>

Your JSON response should contain a normal string such as `"running"`, not a
Python-specific object representation.

</details>

<details>
<summary>Polling interval</summary>

Very short jobs need a shorter polling interval to make progress visible. Avoid
polling more frequently than necessary.

</details>

<details>
<summary>Downloading from fetch()</summary>

The browser can convert the response to a `Blob`, create a temporary object URL,
and trigger an anchor element with the `download` attribute.

</details>

## Self-review questions

Before reading the solution, check:

- Does the create-job endpoint return before the job completes?
- Can a returned `job_id` be used successfully in the status URL?
- Can progress ever exceed `100`?
- What happens if the client requests an unknown job?
- What happens if download is called too early?
- Can the user start the same action repeatedly while it is already running?
- Does invalid client input reach `time.sleep()`?

## Beyond V1

After completing this challenge, consider what must change when:

- The API runs in multiple processes.
- The server restarts.
- A worker crashes halfway through an export.
- Two workers try to claim the same job.
- The generated file is too large to keep in memory.
- One user guesses another user's job ID.

Those concerns belong to later versions of the case.
