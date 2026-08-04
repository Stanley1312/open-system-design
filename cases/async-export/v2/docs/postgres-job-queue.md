# PostgreSQL as a Small Job Queue

V2 stores export requests in a jobs table. The API is a producer: it inserts
pending rows. Worker processes are consumers: each one repeatedly tries to
claim a pending row, performs the simulated export, then persists the result.

This design is intentionally small enough to follow from one HTTP request to
one SQL row. A production system would also need retries, leases, heartbeats,
idempotency, ownership checks, file expiration, and external object storage.
