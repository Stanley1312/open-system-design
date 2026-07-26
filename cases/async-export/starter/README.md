# Async Export V1 — Starter

This directory contains a minimal Flask scaffold for the
[Async Export V1 challenge](../CHALLENGE.md).

## Run

```bash
uv sync
uv run python main.py
```

Open <http://127.0.0.1:5000>.

The initial endpoints deliberately return `501 Not Implemented`. Implement them
in the order suggested by `CHALLENGE.md`.

You are expected to add any frontend files and application modules you need.
A possible final structure is:

```text
starter/
├── main.py
├── async_export.py
├── static/
│   ├── app.js
│   └── styles.css
├── templates/
│   └── index.html
