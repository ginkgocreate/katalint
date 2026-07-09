import json
from pathlib import Path

from typer.testing import CliRunner

import katalint.cli as cli
from katalint.cli import app
from katalint.findings import Finding
from katalint.reporter import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE_ERROR
from katalint.rules.base import Rule


runner = CliRunner()


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class SyntheticConfigRule(Rule):
    id = "KTL900"
    category = "config"

    def check(self, file: Path) -> list[Finding]:
        return [
            Finding(
                rule_id=self.id,
                category=self.category,
                file=file.as_posix(),
                line=1,
                message="Synthetic finding.",
                suggestion="Use this only in tests.",
            )
        ]


def install_synthetic_rule(monkeypatch) -> None:
    monkeypatch.setattr(cli, "load_rules", lambda: [SyntheticConfigRule()])


def test_fail_on_error_keeps_warning_findings_without_failing_ci(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    write_file(tmp_path / "katalint.yml", "version: 1\nfail_on: error\n")
    monkeypatch.chdir(tmp_path)
    install_synthetic_rule(monkeypatch)

    result = runner.invoke(app, ["check", "--format", "json"], catch_exceptions=False)

    assert result.exit_code == EXIT_OK
    payload = json.loads(result.output)
    assert payload[0]["rule_id"] == "KTL900"
    assert payload[0]["severity"] == "warning"


def test_rule_severity_override_can_fail_on_error(tmp_path: Path, monkeypatch) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    write_file(
        tmp_path / "katalint.yml",
        """
version: 1
fail_on: error
rules:
  KTL900:
    severity: error
""".lstrip(),
    )
    monkeypatch.chdir(tmp_path)
    install_synthetic_rule(monkeypatch)

    result = runner.invoke(app, ["check", "--format", "json"], catch_exceptions=False)

    assert result.exit_code == EXIT_FINDINGS
    payload = json.loads(result.output)
    assert payload[0]["severity"] == "error"


def test_inline_suppression_requires_reason(tmp_path: Path, monkeypatch) -> None:
    write_file(
        tmp_path / "AGENTS.md",
        "<!-- katalint-disable KTL900: documented exception -->\n# Agents\n",
    )
    write_file(
        tmp_path / "CLAUDE.md",
        "<!-- katalint-disable KTL900: -->\n# Claude\n",
    )
    monkeypatch.chdir(tmp_path)
    install_synthetic_rule(monkeypatch)

    result = runner.invoke(app, ["check", "--format", "json"], catch_exceptions=False)

    assert result.exit_code == EXIT_FINDINGS
    payload = json.loads(result.output)
    assert [finding["file"] for finding in payload] == ["CLAUDE.md"]


def test_config_ignore_filters_discovered_targets(tmp_path: Path, monkeypatch) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    write_file(tmp_path / "docs/archive/AGENTS.md", "# Ignored\n")
    write_file(tmp_path / "katalint.yml", "version: 1\nignore:\n  - docs/archive/**\n")
    monkeypatch.chdir(tmp_path)
    install_synthetic_rule(monkeypatch)

    result = runner.invoke(
        app,
        ["check", "AGENTS.md", "docs/archive/AGENTS.md", "--format", "json"],
        catch_exceptions=False,
    )

    assert result.exit_code == EXIT_FINDINGS
    payload = json.loads(result.output)
    assert [finding["file"] for finding in payload] == ["AGENTS.md"]


def test_baseline_can_be_written_and_then_filters_matching_findings(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    monkeypatch.chdir(tmp_path)
    install_synthetic_rule(monkeypatch)

    write_result = runner.invoke(
        app,
        ["check", "--write-baseline", "katalint-baseline.json"],
        catch_exceptions=False,
    )
    assert write_result.exit_code == EXIT_OK

    baseline = json.loads((tmp_path / "katalint-baseline.json").read_text(encoding="utf-8"))
    assert baseline["version"] == 1
    assert baseline["findings"][0]["rule_id"] == "KTL900"

    check_result = runner.invoke(
        app,
        ["check", "--baseline", "katalint-baseline.json", "--format", "json"],
        catch_exceptions=False,
    )

    assert check_result.exit_code == EXIT_OK
    assert json.loads(check_result.output) == []


def test_config_targets_override_default_discovery(tmp_path: Path, monkeypatch) -> None:
    write_file(tmp_path / "AGENTS.md", "# Default root target should be skipped\n")
    write_file(tmp_path / "custom/AGENTS.md", "# Custom target\n")
    write_file(
        tmp_path / "katalint.yml",
        """
version: 1
targets:
  agent_configs:
    - custom/AGENTS.md
""".lstrip(),
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "--list-targets"], catch_exceptions=False)

    assert result.exit_code == EXIT_OK
    assert result.output.splitlines() == ["custom/AGENTS.md\tconfig"]


def test_rule_option_override_reconfigures_loaded_rule(tmp_path: Path, monkeypatch) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\nKeep this concise.\n")
    write_file(
        tmp_path / "katalint.yml",
        """
version: 1
rules:
  KTL001:
    max_lines: 1
""".lstrip(),
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "--format", "json"], catch_exceptions=False)

    assert result.exit_code == EXIT_FINDINGS
    payload = json.loads(result.output)
    assert payload[0]["rule_id"] == "KTL001"
    assert "2 lines" in payload[0]["message"]


def test_invalid_config_exits_as_usage_error(tmp_path: Path, monkeypatch) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    write_file(tmp_path / "katalint.yml", "version: 1\nfail_on: never\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check"])

    assert result.exit_code == EXIT_USAGE_ERROR
    assert "config error:" in result.stderr
