# Worker Pool Demo

The interactive demo follows the solution's producer, PostgreSQL queue, worker,
and result flow. It adds worker IDs and read-only dashboard APIs so the browser
can show which worker owns each running job.

Scaling down is graceful. An idle worker stops promptly. A busy worker finishes
its current job, persists the result, and exits before claiming more work. This
avoids abandoning a job in the running state merely because the pool size was
reduced.

The browser polls once per second. WebSockets and server-sent events are omitted
to keep the case focused on the database queue and worker concurrency.
