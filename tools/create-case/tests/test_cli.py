from argparse import Namespace
from pathlib import Path

import pytest
from case_creator import cli
from case_creator.cli import (
    CaseOptions,
    build_file_plan,
    collect_options,
    discover_versions,
    generate,
    slugify,
    suggested_version,
)


def make_options(repo_root: Path, **changes: object) -> CaseOptions:
    values: dict[str, object] = {
        "repo_root": repo_root,
        "case_name": "webhook-delivery",
        "version": "v1",
        "source_version": None,
        "include_demo": False,
        "setup_uv": True,
        "python_version": "3.13",
        "dependencies": ("flask>=3.1",),
        "include_pytest": True,
        "docker_mode": "none",
        "include_postgres": False,
        "create_env_example": False,
        "port": 5000,
        "run_uv_lock": False,
        "dry_run": False,
    }
    values.update(changes)
    return CaseOptions(**values)


def create_repo(tmp_path: Path) -> Path:
    (tmp_path / "cases").mkdir()
    return tmp_path


def test_slugify_creates_kebab_case() -> None:
    assert slugify(" Async Export_v3! ") == "async-export-v3"


def test_discovers_numeric_versions_and_suggests_next(tmp_path: Path) -> None:
    case_dir = tmp_path / "async-export"
    for folder in ("v3", "notes", "v1"):
        (case_dir / folder).mkdir(parents=True)

    assert discover_versions(case_dir) == ["v1", "v3"]
    assert suggested_version(["v1", "v3"]) == "v4"


def test_builds_independent_uv_projects(tmp_path: Path) -> None:
    repo_root = create_repo(tmp_path)
    files = build_file_plan(make_options(repo_root))

    assert "flask>=3.1" in files[Path("starter/pyproject.toml")]
    assert "flask>=3.1" in files[Path("solution/pyproject.toml")]
    assert Path("starter/tests/README.md") in files
    assert Path("solution/tests/README.md") in files
    assert files[Path(".python-version")] == "3.13\n"


def test_inherits_config_without_copying_source_code(tmp_path: Path) -> None:
    repo_root = create_repo(tmp_path)
    source_root = repo_root / "cases/webhook-delivery/v1"
    for component in ("starter", "solution"):
        component_dir = source_root / component
        component_dir.mkdir(parents=True)
        (component_dir / "pyproject.toml").write_text(
            '[project]\nname = "old-name"\nversion = "0.1.0"\n'
            'description = "old"\nrequires-python = ">=3.13"\n'
            'dependencies = ["flask>=3.1"]\n',
            encoding="utf-8",
        )

    options = make_options(
        repo_root,
        version="v2",
        source_version="v1",
        python_version="3.14",
    )
    files = build_file_plan(options)
    project = files[Path("solution/pyproject.toml")]

    assert 'name = "webhook-delivery-v2-solution"' in project
    assert 'requires-python = ">=3.14"' in project
    assert "flask>=3.1" in project
    assert "$3.14" not in project
    assert Path("solution/main.py") in files
    assert "old source" not in files[Path("solution/main.py")]


def test_no_uv_uses_plain_python_instructions(tmp_path: Path) -> None:
    repo_root = create_repo(tmp_path)
    options = make_options(
        repo_root,
        setup_uv=False,
        include_pytest=False,
        dependencies=(),
    )
    files = build_file_plan(options)

    assert Path("solution/pyproject.toml") not in files
    assert "python main.py" in files[Path("solution/README.md")]
    assert "uv sync" not in files[Path("solution/README.md")]


def test_compose_plan_can_include_postgres_and_env_example(tmp_path: Path) -> None:
    repo_root = create_repo(tmp_path)
    options = make_options(
        repo_root,
        docker_mode="compose",
        include_postgres=True,
        create_env_example=True,
        run_uv_lock=False,
    )
    files = build_file_plan(options)

    assert "postgres:16-alpine" in files[Path("compose.yml")]
    assert "DATABASE_URL" in files[Path(".env.example")]
    assert "uv.lock" not in files[Path("solution/Dockerfile")]


def test_generate_refuses_to_overwrite_existing_version(tmp_path: Path) -> None:
    repo_root = create_repo(tmp_path)
    options = make_options(repo_root)
    options.target_dir.mkdir(parents=True)

    with pytest.raises(ValueError, match="refusing to overwrite"):
        generate(options, {Path("README.md"): "new"})


def test_generate_writes_complete_plan(tmp_path: Path) -> None:
    repo_root = create_repo(tmp_path)
    options = make_options(repo_root)
    generate(options, build_file_plan(options))

    assert (options.target_dir / "CHALLENGE.md").is_file()
    assert (options.target_dir / "starter/main.py").is_file()
    assert (options.target_dir / "solution/main.py").is_file()


def test_yes_mode_selects_next_version_without_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = create_repo(tmp_path)
    (repo_root / "cases/async-export/v1").mkdir(parents=True)
    monkeypatch.setattr(cli.shutil, "which", lambda _: None)
    args = Namespace(
        repo=str(repo_root),
        case="async-export",
        version=None,
        from_version=None,
        yes=True,
        dry_run=True,
    )

    options = collect_options(args)

    assert options.version == "v2"
    assert options.source_version == "v1"


def test_dependency_prompt_keeps_commas_inside_requirement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answers = iter(["library>=1,<2", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert cli.ask_dependencies() == ("library>=1,<2",)


def test_rejects_unknown_source_version(tmp_path: Path) -> None:
    repo_root = create_repo(tmp_path)
    (repo_root / "cases/async-export/v1").mkdir(parents=True)
    args = Namespace(
        repo=str(repo_root),
        case="async-export",
        version="v2",
        from_version="v9",
        yes=True,
        dry_run=True,
    )

    with pytest.raises(ValueError, match="Source version v9 does not exist"):
        collect_options(args)


def test_interruption_removes_temporary_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = create_repo(tmp_path)
    options = make_options(repo_root, run_uv_lock=True)

    def interrupt(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli.subprocess, "run", interrupt)

    with pytest.raises(KeyboardInterrupt):
        generate(options, build_file_plan(options))

    assert not options.target_dir.exists()
    assert not list((repo_root / "cases").glob(".webhook-delivery-v1-*"))
