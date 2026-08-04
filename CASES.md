# System Design Case Roadmap

This file tracks potential cases for the repository. Scope and implementation
details will be researched when each case is started.

## Status

- `Available`: challenge and reference solution are ready.
- `Planned`: a likely next case.
- `Backlog`: an idea to evaluate later.

## Cases

| Case                                      | Main concepts                                    |   Difficulty | Status    |
| ----------------------------------------- | ------------------------------------------------ | -----------: | --------- |
| [Async Export V1](cases/async-export/v1/) | Blocking vs async APIs, polling, progress        |     Beginner | Available |
| [Async Export V2](cases/async-export/v2/) | PostgreSQL jobs, real workers, locking           | Intermediate | Available |
| Async Export V3                           | Retry, heartbeat, reaper, checkpoint             | Intermediate | Planned   |
| Multipart File Upload                     | Chunking, parallel upload, resume, checksum      | Intermediate | Backlog   |
| Bulk Data Import                          | Streaming, batch writes, partial failure         | Intermediate | Backlog   |
| Webhook Delivery                          | At-least-once delivery, retry, idempotency, HMAC | Intermediate | Backlog   |
| Notification Service                      | Multiple providers, scheduling, rate limits      | Intermediate | Backlog   |
| Media Processing Pipeline                 | Workflow orchestration, fan-out/fan-in           |     Advanced | Backlog   |
| Order Processing Saga                     | Eventual consistency, compensation, outbox       |     Advanced | Backlog   |

## Suggested order

```text
Async Export V1
      ↓
Async Export V2
      ↓
Async Export V3
      ↓
Multipart File Upload
      ↓
Bulk Data Import
      ↓
Webhook Delivery
      ↓
Notification Service
      ↓
Media Processing Pipeline
      ↓
Order Processing Saga
```

The order is only a guide. A case can move forward when it supports the
concepts currently being studied.
