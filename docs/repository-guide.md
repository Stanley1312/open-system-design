# Repository Guide

## Layout

    open-system-design/
    ├── README.md
    ├── CASES.md
    ├── CONTRIBUTING.md
    ├── Taskfile.yml
    ├── docs/
    │   ├── available-cases.md
    │   ├── async-export-series.md
    │   ├── getting-started.md
    │   ├── learning-approach.md
    │   └── repository-guide.md
    └── cases/
        └── async-export/
            ├── v1/
            │   ├── CHALLENGE.md
            │   ├── starter/
            │   ├── solution/
            │   └── docs/
            └── v2/
                ├── CHALLENGE.md
                ├── starter/
                ├── solution/
                ├── demo/
                └── docs/

## Case conventions

Each learning version should provide:

- README.md for context and entry points;
- CHALLENGE.md for requirements without implementation spoilers;
- starter/ as a minimal scaffold;
- solution/ as a readable reference implementation;
- docs/ for deeper design notes.

A version may include demo/ when extra visualization or observability code would
make the reference solution harder to follow.

Cases remain self-contained. Shared infrastructure belongs at repository level
only when more than one case genuinely needs it.
