# create-case

`create-case` is an interactive CLI wizard (also called a project scaffolder).
It asks a short series of questions, turns the answers into a generation plan,
shows that plan, and only then creates a new case version.

The command is a Python console entry point, not a shell alias. The
`[project.scripts]` section in `pyproject.toml` maps the command name
`create-case` to `case_creator.cli:main`. Installing the package exposes that
command on your `PATH`.

## Run from this repository

Without installing anything globally:

```bash
task create-case
```

Or run the package directly:

```bash
uv run --project tools/create-case create-case --repo .
```

## Install the command

From the repository root:

```bash
uv tool install --editable ./tools/create-case
uv tool update-shell
```

Open a new terminal if your shell path changed, then run:

```bash
create-case
```

`--editable` is useful while developing this repository: changes to the source
are reflected without reinstalling the tool.

## Example flow

```text
$ create-case
Existing cases: async-export
? Case name: async-export
Found async-export: v1, v2
? Version to create [v3]:
? Add an optional demo/ scaffold? [y/N]: y
? Set up Python projects with uv? [Y/n]:
? Inherit dependency config from v2? [Y/n]:
? Python version [3.13]:
? Add pytest as a dev dependency? [Y/n]:
? Docker setup
  1. No Docker files (default)
  2. Dockerfile only
  3. Dockerfile and compose.yml
  Choose a number: 3
? Add a PostgreSQL service to Compose? [y/N]: y
? Create .env.example? [Y/n]:
? Application port [5000]:
? Generate uv.lock files now? [Y/n]:

Plan
  Target: .../cases/async-export/v3
  Source config: v2
  Demo: yes
  uv: yes
  Docker: compose
? Create this case version? [Y/n]:
```

Choosing inheritance copies only project configuration such as dependencies;
it does not copy owner source code from the previous version.

## Automation and preview

Preview without writing files:

```bash
create-case --case async-export --version v3 --dry-run
```

Accept conservative defaults for scripts or CI:

```bash
create-case --case async-export --version v3 --yes
```

With `--yes`, the tool creates starter and solution uv projects with pytest,
inherits the latest version when available, and does not add demo or Docker
files. If `--version` is omitted, it selects the next numeric version.

## Safety rules

- Existing version folders are never overwritten.
- Files are assembled in a temporary folder and moved into place atomically.
- Cancelling before confirmation writes nothing.
- Only `.env.example` may be generated; real `.env` files and secrets are not.
- `--dry-run` prints every planned file without creating the case.

Generated starter and solution projects stay independent. This intentionally
preserves the repository's learning-oriented layout while removing repetitive
setup work.
