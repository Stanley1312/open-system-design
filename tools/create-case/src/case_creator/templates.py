"""Small text templates used by the case creator.

Templates are plain Python functions so learners can read how every generated
file is assembled without learning a template engine first.
"""

import json
import re


def project_file(
    project_name: str,
    description: str,
    python_version: str,
    dependencies: list[str],
    include_pytest: bool,
) -> str:
    dependency_lines = "\n".join(
        f"    {json.dumps(dependency)}," for dependency in dependencies
    )
    if dependency_lines:
        dependency_block = f"[\n{dependency_lines}\n]"
    else:
        dependency_block = "[]"

    content = (
        "[project]\n"
        f'name = "{project_name}"\n'
        'version = "0.1.0"\n'
        f"description = {json.dumps(description)}\n"
        'readme = "README.md"\n'
        f'requires-python = ">={python_version}"\n'
        f"dependencies = {dependency_block}\n"
    )
    if include_pytest:
        content += '\n[dependency-groups]\ndev = ["pytest>=8.4.2"]\n'
    return content


def inherited_project_file(
    source: str,
    project_name: str,
    description: str,
    python_version: str,
    include_pytest: bool,
) -> str:
    content = re.sub(
        r'^name = ".*"$',
        f'name = "{project_name}"',
        source,
        count=1,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r'^description = ".*"$',
        f"description = {json.dumps(description)}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r'^requires-python = ".*"$',
        f'requires-python = ">={python_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if (
        include_pytest
        and "pytest" not in content
        and "[dependency-groups]" not in content
    ):
        content += '\n[dependency-groups]\ndev = ["pytest>=8.4.2"]\n'
    return content if content.endswith("\n") else content + "\n"


def version_readme(case_name: str, version: str) -> str:
    title = case_name.replace("-", " ").title()
    return f"""# {title} {version.upper()}

This version is a new system design learning step.

## Start here

1. Define the limitation inherited from the previous version.
2. Read CHALLENGE.md.
3. Implement the exercise in starter/.
4. Compare it with solution/.
5. Record deeper trade-offs in docs/.

Keep the request flow explicit and document intentional shortcuts.
"""


def challenge(case_name: str, version: str) -> str:
    title = case_name.replace("-", " ").title()
    return f"""# {title} {version.upper()} Challenge

## Learning goal

TODO: Describe the single major system design idea introduced in this version.

## Requirements

- TODO: Define observable behavior before implementation details.
- TODO: Include success, validation, and failure boundaries.
- TODO: State what is intentionally out of scope.
"""


def component_readme(
    case_name: str,
    version: str,
    component: str,
    use_uv: bool,
) -> str:
    title = case_name.replace("-", " ").title()
    purpose = (
        "Complete the TODOs without reading the reference solution first."
        if component == "starter"
        else "This directory contains the owner reference implementation."
    )
    run_command = (
        "    uv sync\n    uv run python main.py" if use_uv else "    python main.py"
    )
    return f"""# {title} {version.upper()} — {component.title()}

{purpose}

## Run

{run_command}
"""


def component_main(case_name: str, version: str, component: str) -> str:
    return f'''"""{component.title()} entry point for {case_name} {version}."""


def main() -> None:
    print("{case_name} {version} {component}: ready to implement")


if __name__ == "__main__":
    main()
'''


def demo_readme(case_name: str, version: str) -> str:
    title = case_name.replace("-", " ").title()
    return f"""# {title} {version.upper()} — Interactive Demo

This optional demo may add observability or UI code without making the owner
solution harder to read. Document every intentional difference from solution/.
"""


def docs_readme(case_name: str, version: str) -> str:
    title = case_name.replace("-", " ").title()
    return f"""# {title} {version.upper()} Design Notes

Use this directory for notes that explain trade-offs, failure modes, and why the
next architectural component is necessary.
"""


def dockerfile(
    use_uv: bool,
    python_version: str,
    has_uv_lock: bool,
) -> str:
    if use_uv:
        install = (
            "COPY pyproject.toml uv.lock README.md ./\n"
            "RUN uv sync --frozen --no-dev --no-install-project"
            if has_uv_lock
            else "COPY pyproject.toml README.md ./\n"
            "RUN uv sync --no-dev --no-install-project"
        )
        return f"""FROM ghcr.io/astral-sh/uv:python{python_version}-bookworm-slim

WORKDIR /app

{install}

COPY . .

CMD ["uv", "run", "--no-sync", "python", "main.py"]
"""

    return f"""FROM python:{python_version}-slim

WORKDIR /app
COPY . .

CMD ["python", "main.py"]
"""


def compose_file(port: int, include_postgres: bool) -> str:
    database = ""
    dependency = ""
    environment = ""

    if include_postgres:
        database = """
  database:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 1s
      timeout: 3s
      retries: 20
"""
        dependency = """
    depends_on:
      database:
        condition: service_healthy"""
        environment = """
    environment:
      DATABASE_URL: postgresql://app:app@database:5432/app"""

    return f"""services:
  app:
    build:
      context: ./solution
    ports:
      - "{port}:{port}"{environment}{dependency}
{database}"""


def env_example(include_postgres: bool) -> str:
    if include_postgres:
        return (
            "POSTGRES_DB=app\n"
            "POSTGRES_USER=app\n"
            "POSTGRES_PASSWORD=change-me\n"
            "DATABASE_URL=postgresql://app:change-me@localhost:5432/app\n"
        )
    return "# Add non-secret local configuration here.\n"
