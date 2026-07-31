# Async Export V1 — Starter

Start by experiencing the problem. This scaffold already implements a slow
synchronous export so you have something meaningful to run before writing code.

## 1. Run the Baseline

```bash
uv sync
uv run python main.py
```

Open <http://127.0.0.1:5000>, choose five seconds, and download the report.
Notice that the request stays open and exposes no progress until the file is
ready.

## 2. Ask the Design Question

Must the user keep an HTTP request open while the server performs long-running
work? Read [`../CHALLENGE.md`](../CHALLENGE.md) and replace that interaction with
an asynchronous job flow, one endpoint at a time. The challenge covers backend
code only; you do not need to modify the provided UI.

## Source Map

```text
starter/
├── main.py              # runnable sync baseline; add three async routes here
├── static/
│   ├── app.js           # provided sync experiment; no changes required
│   └── styles.css
└── templates/
    └── index.html       # problem explanation and experiment UI
```

Keep the complete flow easy to trace. New modules are optional; introduce one
only when it makes the behavior easier to understand.
