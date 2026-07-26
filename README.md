# Open System Design

Learn system design by implementing concrete, runnable cases.

Instead of starting with architecture diagrams alone, each case begins with a
small working problem. You can implement the challenge yourself, compare it
with the reference solution, and then study how the design should evolve as
scale and reliability requirements increase.

## Cases

| Case | Concepts | Status |
|---|---|---|
| [Async Export V1](cases/async-export/) | Long-running requests, job APIs, polling, progress, file download | Available |

## How to use this repository

1. Open a case and read its `README.md`.
2. Work through `CHALLENGE.md` without reading the solution first.
3. Run and test your implementation.
4. Compare your decisions with the reference solution.
5. Read the design note and identify what the next version must improve.

Each version focuses on a limited set of ideas. Early versions may intentionally
use in-memory state or simulated delays so the core interaction remains easy to
understand. Later versions can introduce databases, workers, retries, locking,
checkpoints, and object storage.

## Learning philosophy

A system design component should be added because a concrete limitation requires
it—not merely because it appears in a typical architecture diagram.

The code in this repository favors clarity and observable behavior over
production completeness. Each case documents its intentional limitations.
