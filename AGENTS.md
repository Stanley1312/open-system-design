# Repository Guidelines

## Project Structure & Module Organization

This repository teaches system design through runnable cases. Repository-level
documentation lives in `README.md`, `CASES.md`, and `CONTRIBUTING.md`. Each case
belongs under `cases/<case-name>/` and should keep the same learning-oriented
layout:

- `README.md` introduces the case and its workflow.
- `CHALLENGE.md` defines requirements without revealing the implementation.
- `starter/` contains the minimal scaffold learners extend.
- `solution/` contains the reference implementation and its own dependencies.
- `docs/` holds deeper design notes.

For example, `cases/async-export/solution/async_export.py` defines the Flask
application, while `templates/` and `static/` contain its HTML, JavaScript, and
CSS assets. Keep cases self-contained; do not introduce shared infrastructure
until more than one case genuinely needs it.

## Build, Test, and Development Commands

The Python examples require Python 3.13+ and use `uv`. Run commands from the
specific project directory because starter and solution dependencies are
separate:

```bash
cd cases/async-export/solution
uv sync                    # install dependencies from pyproject.toml/uv.lock
uv run python main.py      # start Flask at http://127.0.0.1:5000
```

Use the same commands under `starter/` when working through the challenge.
There is no repository-wide build command or committed automated test command.

## Coding Style & Naming Conventions

Follow standard Python style: four-space indentation, `snake_case` for modules,
functions, and variables, `PascalCase` for classes, and uppercase constants.
Add type hints where they clarify API boundaries. Keep route handlers and the
browser flow small and explicit so learners can trace an HTTP request end to
end. Use kebab-case for case directories (for example, `async-export`) and
descriptive lowercase names for frontend files. No formatter or linter is
currently configured; match surrounding code and keep imports grouped.

## Testing Guidelines

New behavior should include focused tests, preferably with `pytest` and Flask's
test client. Place them in a local `tests/` directory and name files
`test_<feature>.py`. Cover successful flows, validation boundaries, unknown job
IDs, premature downloads, and progress caps. Until tests are added, manually
exercise both sync and async paths in the browser and verify relevant HTTP
status codes.

## Commit & Pull Request Guidelines

History uses short Conventional Commit-style subjects such as `feat:`, `docs:`,
`refactor:`, and `chore:`. Keep each commit scoped to one coherent change and
write the subject in imperative form. Pull requests should explain the learning
goal, list verification steps, link any issue, and call out intentional V1
limitations. Include screenshots or a short recording for visible UI changes,
and update case documentation whenever behavior or commands change.
