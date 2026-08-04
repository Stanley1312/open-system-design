# Async Export V2 — Owner Solution

This directory contains the original V2 implementation. Its Python and SQL
source files were moved here without modifying their contents so learners can
compare their work against the owner flow.

## Run

    uv sync
    ./run_db.sh
    uv run python main.py

For the observable worker-pool dashboard, use:

    ../run_demo.sh

The demo is a separate implementation and does not import these files.
