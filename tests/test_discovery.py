from pathlib import Path

from typer.testing import CliRunner

from katalint import __version__
from katalint.cli import app
from katalint.discovery import Target, discover_targets


runner = CliRunner()


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def paths_by_kind(targets: list[Target]) -> dict[str, str]:
    return {target.path.as_posix(): target.kind for target in targets}


def test_default_discovery_classifies_targets_by_path_and_frontmatter(tmp_path: Path) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    write_file(tmp_path / "AGENTS.override.md", "# Local override\n")
    write_file(tmp_path / "CLAUDE.md", "# Claude\n")
    write_file(tmp_path / ".claude/agents/reviewer.md", "---\nname: reviewer\n---\n")
    write_file(tmp_path / ".agent/tasks/fix-parser.md", "---\ntype: task\n---\n# Fix\n")
    write_file(
        tmp_path / "docs/agent/handoffs/2026-07-07.md",
        "---\ntype: handoff\n---\n# Handoff\n",
    )
    write_file(tmp_path / "docs/agent/tasks/missing-frontmatter.md", "# Not a task\n")
    write_file(tmp_path / "vendor/AGENTS.md", "# Ignored\n")
    write_file(tmp_path / "node_modules/pkg/CLAUDE.md", "# Ignored\n")

    targets = discover_targets(root=tmp_path)

    assert paths_by_kind(targets) == {
        ".agent/tasks/fix-parser.md": "task",
        ".claude/agents/reviewer.md": "config",
        "AGENTS.md": "config",
        "AGENTS.override.md": "config",
        "CLAUDE.md": "config",
        "docs/agent/handoffs/2026-07-07.md": "handoff",
        "docs/agent/tasks/missing-frontmatter.md": "unknown",
    }


def test_absent_agents_override_is_not_an_error(tmp_path: Path) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")

    targets = discover_targets(root=tmp_path)

    assert paths_by_kind(targets) == {"AGENTS.md": "config"}


def test_task_and_handoff_paths_without_frontmatter_are_unknown(tmp_path: Path) -> None:
    write_file(tmp_path / ".agent/tasks/no-frontmatter.md", "# Task shaped path\n")
    write_file(tmp_path / "docs/agent/handoffs/no-frontmatter.md", "# Handoff shaped path\n")

    targets = discover_targets(root=tmp_path)

    assert paths_by_kind(targets) == {
        ".agent/tasks/no-frontmatter.md": "unknown",
        "docs/agent/handoffs/no-frontmatter.md": "unknown",
    }


def test_explicit_single_file_is_accepted(tmp_path: Path) -> None:
    agents = tmp_path / "AGENTS.md"
    write_file(agents, "# Agents\n")

    targets = discover_targets(paths=[agents], root=tmp_path)

    assert paths_by_kind(targets) == {"AGENTS.md": "config"}


def test_explicit_directory_discovers_markdown_and_applies_ignore(tmp_path: Path) -> None:
    write_file(tmp_path / "docs/notes.md", "# Notes\n")
    write_file(tmp_path / "docs/agent/tasks/typed.md", "---\ntype: task\n---\n# Task\n")
    write_file(tmp_path / "docs/node_modules/ignored.md", "# Ignored\n")

    targets = discover_targets(paths=[tmp_path / "docs"], root=tmp_path)

    assert paths_by_kind(targets) == {
        "docs/agent/tasks/typed.md": "task",
        "docs/notes.md": "unknown",
    }


def test_cli_version_returns_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == __version__


def test_cli_check_list_targets_outputs_path_and_kind(tmp_path: Path, monkeypatch) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    write_file(tmp_path / ".agent/tasks/fix.md", "---\ntype: task\n---\n# Fix\n")
    write_file(tmp_path / "docs/agent/tasks/no-frontmatter.md", "# Not a task\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "--list-targets"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        ".agent/tasks/fix.md\ttask",
        "AGENTS.md\tconfig",
        "docs/agent/tasks/no-frontmatter.md\tunknown",
    ]


def test_cli_check_accepts_explicit_single_file(tmp_path: Path, monkeypatch) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "AGENTS.md", "--list-targets"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output.strip() == "AGENTS.md\tconfig"
