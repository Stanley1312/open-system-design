# Getting Started

## Prerequisites

- Python 3.13 or newer.
- [uv](https://docs.astral.sh/uv/) for Python environments and dependencies.
- Docker with Docker Compose for the V2 interactive demo.
- [Task](https://taskfile.dev/) for repository-level shortcuts.

You can enter a case directory and run its underlying commands directly if you
do not use Task.

## Repository commands

List all available shortcuts from the repository root:

    task --list

Run the V1 reference solution:

    task v1:solution

Open http://127.0.0.1:5000 to compare synchronous and asynchronous export
behavior.

Run the V2 interactive worker dashboard:

    task v2:demo

Open http://127.0.0.1:5000. The command builds and starts a temporary PostgreSQL
database together with the Flask demo application.

From the dashboard you can create multiple jobs, inspect the pending queue, see
worker ownership, change the process count, follow progress, and download
completed exports.

Stop the V2 demo with Ctrl+C, or from another terminal:

    task v2:demo:down

Follow its logs with:

    task v2:demo:logs

The demo database uses temporary storage. A complete Compose shutdown clears
its jobs so the next run starts with an empty queue.
