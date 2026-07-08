from __future__ import annotations

from pathlib import Path
import subprocess

from typer.testing import CliRunner

from katalint.cli import app
from katalint.reporter import EXIT_FINDINGS, EXIT_OK
from katalint.rules.init_fossilization import InitFossilizationRule


runner = CliRunner()


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", ".")
    git(
        repo,
        "-c",
        "user.name=katalint-tests",
        "-c",
        "user.email=katalint@example.invalid",
        "commit",
        "-m",
        message,
    )


def init_repo(repo: Path) -> None:
    git(repo, "init", "-b", "main")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def add_repo_activity(repo: Path, count: int) -> None:
    src_dir = repo / "src"
    start = len(list(src_dir.glob("module_*.py"))) if src_dir.exists() else 0
    for index in range(count):
        module_index = start + index
        write(repo / "src" / f"module_{module_index}.py", f"VALUE = {module_index}\n")
        commit_all(repo, f"code change {module_index}")


def test_stale_agents_file_is_flagged_when_repo_keeps_changing(tmp_path: Path) -> None:
    init_repo(tmp_path)
    agents = tmp_path / "AGENTS.md"
    write(agents, "# Agents\n")
    commit_all(tmp_path, "add agents")
    add_repo_activity(tmp_path, 7)

    findings = InitFossilizationRule().check(agents)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "KTL004"
    assert finding.category == "config"
    assert finding.severity == "warning"
    assert "1 update" in finding.message
    assert "8 repository commits" in finding.message


def test_config_updated_twice_is_not_flagged(tmp_path: Path) -> None:
    init_repo(tmp_path)
    agents = tmp_path / "AGENTS.md"
    write(agents, "# Agents\n")
    commit_all(tmp_path, "add agents")
    add_repo_activity(tmp_path, 3)
    write(agents, "# Agents\n\nUpdated guidance.\n")
    commit_all(tmp_path, "update agents")
    add_repo_activity(tmp_path, 4)

    assert InitFossilizationRule().check(agents) == []


def test_young_repo_is_not_flagged(tmp_path: Path) -> None:
    init_repo(tmp_path)
    agents = tmp_path / "AGENTS.md"
    write(agents, "# Agents\n")
    commit_all(tmp_path, "add agents")
    add_repo_activity(tmp_path, 2)

    assert InitFossilizationRule().check(agents) == []


def test_non_git_file_is_skipped(tmp_path: Path) -> None:
    agents = tmp_path / "AGENTS.md"
    write(agents, "# Agents\n")

    assert InitFossilizationRule().check(agents) == []


def test_only_agents_and_claude_are_checked(tmp_path: Path) -> None:
    init_repo(tmp_path)
    override = tmp_path / "AGENTS.override.md"
    write(override, "# Override\n")
    commit_all(tmp_path, "add override")
    add_repo_activity(tmp_path, 7)

    assert InitFossilizationRule().check(override) == []


def test_applies_to_config_only() -> None:
    rule = InitFossilizationRule()

    assert rule.applies_to("config") is True
    assert rule.applies_to("task") is False
    assert rule.applies_to("handoff") is False
    assert rule.applies_to("unknown") is False


def test_cli_reports_init_fossilization(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    agents = tmp_path / "AGENTS.md"
    write(agents, "# Agents\n")
    commit_all(tmp_path, "add agents")
    add_repo_activity(tmp_path, 7)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "--format", "text"], catch_exceptions=False)

    assert result.exit_code == EXIT_FINDINGS
    assert "warning KTL004 config/init-fossilization" in result.output
    assert "AGENTS.md has 1 update" in result.output


def test_cli_explain_reads_init_fossilization_doc() -> None:
    result = runner.invoke(app, ["explain", "KTL004"], catch_exceptions=False)

    assert result.exit_code == EXIT_OK
    assert "# KTL004: Init Fossilization" in result.output


def test_cli_non_git_repo_still_exits_zero(tmp_path: Path, monkeypatch) -> None:
    write(tmp_path / "AGENTS.md", "# Agents\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "--format", "json"], catch_exceptions=False)

    assert result.exit_code == EXIT_OK
    assert result.output.strip() == "[]"
