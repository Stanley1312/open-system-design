"""Interactive command for creating a new case or case version."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from case_creator import templates

CASE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^v[1-9][0-9]*$")


class WizardCancelled(Exception):
    """Raised when the user cancels the wizard."""


@dataclass(frozen=True)
class CaseOptions:
    repo_root: Path
    case_name: str
    version: str
    source_version: str | None
    include_demo: bool
    setup_uv: bool
    python_version: str
    dependencies: tuple[str, ...]
    include_pytest: bool
    docker_mode: str
    include_postgres: bool
    create_env_example: bool
    port: int
    run_uv_lock: bool
    dry_run: bool

    @property
    def case_dir(self) -> Path:
        return self.repo_root / "cases" / self.case_name

    @property
    def target_dir(self) -> Path:
        return self.case_dir / self.version


def slugify(value: str) -> str:
    value = value.strip().lower().replace("_", "-").replace(" ", "-")
    value = re.sub(r"[^a-z0-9-]", "", value)
    return re.sub(r"-+", "-", value).strip("-")


def version_number(version: str) -> int:
    return int(version[1:])


def discover_versions(case_dir: Path) -> list[str]:
    if not case_dir.is_dir():
        return []
    versions = [
        path.name
        for path in case_dir.iterdir()
        if path.is_dir() and VERSION_PATTERN.fullmatch(path.name)
    ]
    return sorted(versions, key=version_number)


def suggested_version(versions: list[str]) -> str:
    if not versions:
        return "v1"
    return f"v{version_number(versions[-1]) + 1}"


def find_repo_root(explicit_path: str | None) -> Path:
    if explicit_path:
        root = Path(explicit_path).expanduser().resolve()
    else:
        root = Path.cwd().resolve()
        for candidate in [root, *root.parents]:
            if (candidate / "cases").is_dir() and (candidate / ".git").exists():
                root = candidate
                break

    if not (root / "cases").is_dir():
        raise ValueError(
            "Repository root must contain a cases/ directory. "
            "Use --repo when running outside the repository."
        )
    return root


def ask_text(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        answer = input(f"? {prompt}{suffix}: ").strip()
        if answer:
            return answer
        if default is not None:
            return default
        print("  Please enter a value.")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        answer = input(f"? {prompt} [{suffix}]: ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("  Enter y or n.")


def ask_choice(prompt: str, choices: list[tuple[str, str]], default: str) -> str:
    print(f"? {prompt}")
    for index, (value, label) in enumerate(choices, start=1):
        marker = " (default)" if value == default else ""
        print(f"  {index}. {label}{marker}")

    while True:
        answer = input("  Choose a number: ").strip()
        if not answer:
            return default
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1][0]
        print(f"  Enter a number from 1 to {len(choices)}.")


def inherited_python_version(case_dir: Path, source_version: str | None) -> str:
    if source_version is None:
        return "3.13"

    source = case_dir / source_version
    candidates = [
        source / ".python-version",
        source / "solution" / ".python-version",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    return "3.13"


def ask_dependencies() -> tuple[str, ...]:
    print("? Runtime dependencies (press Enter on an empty value to finish)")
    dependencies: list[str] = []
    while True:
        dependency = ask_text("Dependency", "")
        if not dependency:
            return tuple(dependencies)
        dependencies.append(dependency)


def collect_options(args: argparse.Namespace) -> CaseOptions:
    repo_root = find_repo_root(args.repo)
    cases_root = repo_root / "cases"
    existing_cases = sorted(path.name for path in cases_root.iterdir() if path.is_dir())

    if existing_cases:
        print("Existing cases: " + ", ".join(existing_cases))

    raw_case_name = args.case or ask_text("Case name")
    case_name = slugify(raw_case_name)
    if not case_name or not CASE_PATTERN.fullmatch(case_name):
        raise ValueError("Case name must become a non-empty kebab-case slug")
    if case_name != raw_case_name:
        print(f'  Using folder name "{case_name}".')

    case_dir = cases_root / case_name
    versions = discover_versions(case_dir)
    if args.from_version and args.from_version not in versions:
        raise ValueError(
            f"Source version {args.from_version} does not exist in {case_name}"
        )

    if versions:
        print(f"Found {case_name}: " + ", ".join(versions))
    else:
        print(f'Case "{case_name}" does not exist yet; it will be created.')

    default_version = suggested_version(versions)
    version = args.version or (
        default_version if args.yes else ask_text("Version to create", default_version)
    )
    version = version.strip().lower()
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("Version must look like v1, v2, or v3")
    if (case_dir / version).exists():
        raise ValueError(f"{case_name}/{version} already exists; nothing was changed")

    if args.yes:
        include_demo = False
        setup_uv = True
    else:
        include_demo = ask_yes_no("Add an optional demo/ scaffold?", False)
        setup_uv = ask_yes_no("Set up Python projects with uv?", True)

    source_version = None
    if setup_uv and versions:
        requested_source = args.from_version or versions[-1]
        inherit = (
            True
            if args.from_version or args.yes
            else ask_yes_no(
                f"Inherit dependency config from {requested_source}?",
                True,
            )
        )
        if inherit:
            source_version = requested_source
            if source_version not in versions:
                raise ValueError(
                    f"Source version {source_version} does not exist in {case_name}"
                )

    default_python = inherited_python_version(case_dir, source_version)
    python_version = (
        default_python
        if args.yes or not setup_uv
        else ask_text("Python version", default_python)
    )

    dependencies: tuple[str, ...] = ()
    if setup_uv and source_version is None and not args.yes:
        dependencies = ask_dependencies()

    include_pytest = setup_uv and (
        True if args.yes else ask_yes_no("Add pytest as a dev dependency?", True)
    )

    if args.yes:
        docker_mode = "none"
    else:
        docker_mode = ask_choice(
            "Docker setup",
            [
                ("none", "No Docker files"),
                ("dockerfile", "Dockerfile only"),
                ("compose", "Dockerfile and compose.yml"),
            ],
            "none",
        )

    include_postgres = docker_mode == "compose" and (
        False if args.yes else ask_yes_no("Add a PostgreSQL service to Compose?", False)
    )
    create_env_example = (docker_mode != "none" or include_postgres) and (
        True if args.yes else ask_yes_no("Create .env.example?", True)
    )

    port = 5000
    if docker_mode == "compose" and not args.yes:
        raw_port = ask_text("Application port", "5000")
        if not raw_port.isdigit() or not 1 <= int(raw_port) <= 65535:
            raise ValueError("Port must be an integer between 1 and 65535")
        port = int(raw_port)

    uv_available = shutil.which("uv") is not None
    run_uv_lock = (
        setup_uv
        and uv_available
        and (True if args.yes else ask_yes_no("Generate uv.lock files now?", True))
    )
    if setup_uv and not uv_available:
        print("  uv was not found. pyproject.toml will be created without uv.lock.")

    return CaseOptions(
        repo_root=repo_root,
        case_name=case_name,
        version=version,
        source_version=source_version,
        include_demo=include_demo,
        setup_uv=setup_uv,
        python_version=python_version,
        dependencies=dependencies,
        include_pytest=include_pytest,
        docker_mode=docker_mode,
        include_postgres=include_postgres,
        create_env_example=create_env_example,
        port=port,
        run_uv_lock=run_uv_lock,
        dry_run=args.dry_run,
    )


def project_name(options: CaseOptions, component: str) -> str:
    return f"{options.case_name}-{options.version}-{component}"


def project_description(options: CaseOptions, component: str) -> str:
    return (
        f"{component.title()} project for {options.case_name} {options.version.upper()}"
    )


def source_project_file(
    options: CaseOptions,
    component: str,
) -> Path | None:
    if options.source_version is None:
        return None

    source_root = options.case_dir / options.source_version
    direct = source_root / component / "pyproject.toml"
    if direct.is_file():
        return direct

    fallback = source_root / "solution" / "pyproject.toml"
    return fallback if fallback.is_file() else None


def build_file_plan(options: CaseOptions) -> dict[Path, str]:
    files: dict[Path, str] = {
        Path("README.md"): templates.version_readme(
            options.case_name,
            options.version,
        ),
        Path("CHALLENGE.md"): templates.challenge(
            options.case_name,
            options.version,
        ),
        Path("docs/README.md"): templates.docs_readme(
            options.case_name,
            options.version,
        ),
    }

    components = ["starter", "solution"]
    if options.include_demo:
        components.append("demo")

    for component in components:
        files[Path(component) / "README.md"] = (
            templates.demo_readme(options.case_name, options.version)
            if component == "demo"
            else templates.component_readme(
                options.case_name,
                options.version,
                component,
                options.setup_uv,
            )
        )
        files[Path(component) / "main.py"] = templates.component_main(
            options.case_name,
            options.version,
            component,
        )

        if not options.setup_uv:
            continue

        source_file = source_project_file(options, component)
        if source_file is not None:
            project_content = templates.inherited_project_file(
                source_file.read_text(encoding="utf-8"),
                project_name(options, component),
                project_description(options, component),
                options.python_version,
                options.include_pytest,
            )
        else:
            project_content = templates.project_file(
                project_name(options, component),
                project_description(options, component),
                options.python_version,
                list(options.dependencies),
                options.include_pytest,
            )

        files[Path(component) / "pyproject.toml"] = project_content
        if options.include_pytest:
            files[Path(component) / "tests/README.md"] = (
                "# Tests\n\nAdd focused tests for the behavior introduced here.\n"
            )

    if options.setup_uv:
        files[Path(".python-version")] = options.python_version + "\n"

    if options.docker_mode != "none":
        files[Path("solution/Dockerfile")] = templates.dockerfile(
            options.setup_uv,
            options.python_version,
            options.run_uv_lock,
        )
    if options.docker_mode == "compose":
        files[Path("compose.yml")] = templates.compose_file(
            options.port,
            options.include_postgres,
        )
    if options.create_env_example:
        files[Path(".env.example")] = templates.env_example(options.include_postgres)

    return files


def print_summary(options: CaseOptions, files: dict[Path, str]) -> None:
    print("\nPlan")
    print(f"  Target: {options.target_dir}")
    print(f"  Source config: {options.source_version or 'fresh'}")
    print(f"  Demo: {'yes' if options.include_demo else 'no'}")
    print(f"  uv: {'yes' if options.setup_uv else 'no'}")
    print(f"  Docker: {options.docker_mode}")
    print(f"  Files: {len(files)}")


def generate(options: CaseOptions, files: dict[Path, str]) -> None:
    if options.target_dir.exists():
        raise ValueError(f"{options.target_dir} already exists; refusing to overwrite")

    if options.dry_run:
        print("\nDry run — no files were written:")
        for relative_path in sorted(files, key=str):
            print(f"  {relative_path}")
        return

    cases_root = options.repo_root / "cases"
    temporary_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{options.case_name}-{options.version}-",
            dir=cases_root,
        )
    )

    try:
        for relative_path, content in files.items():
            destination = temporary_dir / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

        if options.run_uv_lock:
            components = ["starter", "solution"]
            if options.include_demo:
                components.append("demo")
            for component in components:
                subprocess.run(
                    ["uv", "lock", "--project", str(temporary_dir / component)],
                    check=True,
                )

        options.case_dir.mkdir(parents=True, exist_ok=True)
        os.replace(temporary_dir, options.target_dir)
    except BaseException:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        if options.case_dir.is_dir() and not any(options.case_dir.iterdir()):
            options.case_dir.rmdir()
        raise

    print(f"\nCreated {options.target_dir}")
    print("Next:")
    print("  1. Define the learning goal in CHALLENGE.md.")
    print("  2. Add TODOs to starter/.")
    print("  3. Implement the owner flow in solution/.")
    print("  4. Update CASES.md when the version is ready.")


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        prog="create-case",
        description="Interactively create a system design case version.",
    )
    command.add_argument("--repo", help="Repository root; defaults to current repo")
    command.add_argument("--case", help="Case name, for example async-export")
    command.add_argument("--version", help="Version to create, for example v3")
    command.add_argument(
        "--from-version",
        help="Version whose dependency config should be inherited",
    )
    command.add_argument(
        "--yes",
        action="store_true",
        help="Accept safe defaults; requires --case; selects the next version",
    )
    command.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the generation plan without writing files",
    )
    return command


def main() -> int:
    args = parser().parse_args()
    if args.yes and not args.case:
        print("error: --yes requires --case", file=sys.stderr)
        return 2

    try:
        options = collect_options(args)
        files = build_file_plan(options)
        print_summary(options, files)

        if (
            not args.yes
            and not options.dry_run
            and not ask_yes_no("Create this case version?", True)
        ):
            raise WizardCancelled

        generate(options, files)
        return 0
    except (KeyboardInterrupt, EOFError, WizardCancelled):
        print("\nCancelled. No files were changed.")
        return 130
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
