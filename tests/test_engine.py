import json
from pathlib import Path

from typer.testing import CliRunner

import katalint.cli as cli
from katalint.cli import app
from katalint.findings import Finding
from katalint.reporter import (
    EXIT_FINDINGS,
    EXIT_INTERNAL_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    exit_code_for_findings,
    render_findings,
)
from katalint.rules.base import Rule, load_rules


runner = CliRunner()


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sample_finding() -> Finding:
    return Finding(
        rule_id="KTL900",
        category="config",
        file="AGENTS.md",
        line=1,
        message="Synthetic finding.",
        suggestion="Use this only in tests.",
    )


def test_finding_defaults_to_warning_and_serializes_all_fields() -> None:
    finding = sample_finding()

    assert finding.severity == "warning"
    assert finding.to_dict() == {
        "rule_id": "KTL900",
        "category": "config",
        "severity": "warning",
        "file": "AGENTS.md",
        "line": 1,
        "message": "Synthetic finding.",
        "suggestion": "Use this only in tests.",
    }


def test_reporter_renders_text_and_json_with_exit_codes() -> None:
    finding = sample_finding()

    text = render_findings([finding], output_format="text")
    assert text.splitlines() == [
        "AGENTS.md",
        "  warning KTL900 config/synthetic-finding",
        "  Synthetic finding.",
        "  Suggestion: Use this only in tests.",
    ]

    payload = json.loads(render_findings([finding], output_format="json"))
    assert payload == [finding.to_dict()]

    assert exit_code_for_findings([]) == EXIT_OK == 0
    assert exit_code_for_findings([finding]) == EXIT_FINDINGS == 1
    assert EXIT_USAGE_ERROR == 2
    assert EXIT_INTERNAL_ERROR == 3


def test_rule_registry_auto_discovers_added_rule_files(tmp_path: Path, monkeypatch) -> None:
    package_dir = tmp_path / "sample_rules"
    write_file(package_dir / "__init__.py")
    write_file(
        package_dir / "ktl900_noop.py",
        """
from pathlib import Path

from katalint.findings import Finding
from katalint.rules.base import Rule


class NoopConfigRule(Rule):
    id = "KTL900"
    category = "config"

    def check(self, file: Path) -> list[Finding]:
        return []
""".lstrip(),
    )
    monkeypatch.syspath_prepend(tmp_path)

    rules = load_rules(package_name="sample_rules")

    assert [rule.id for rule in rules] == ["KTL900"]
    assert rules[0].applies_to("config")
    assert not rules[0].applies_to("task")


def test_rule_default_applies_to_uses_category_boundaries() -> None:
    class ConfigRule(Rule):
        id = "KTL901"
        category = "config"

    class WorkflowRule(Rule):
        id = "KTL902"
        category = "workflow"

    config_rule = ConfigRule()
    workflow_rule = WorkflowRule()

    assert config_rule.applies_to("config")
    assert not config_rule.applies_to("task")
    assert not config_rule.applies_to("handoff")
    assert workflow_rule.applies_to("task")
    assert workflow_rule.applies_to("handoff")
    assert not workflow_rule.applies_to("config")


def test_cli_check_completes_with_zero_rules_for_text_and_json(tmp_path: Path, monkeypatch) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    monkeypatch.chdir(tmp_path)

    text_result = runner.invoke(app, ["check", "--format", "text"], catch_exceptions=False)
    json_result = runner.invoke(app, ["check", "--format", "json"], catch_exceptions=False)

    assert text_result.exit_code == EXIT_OK
    assert text_result.output == ""
    assert json_result.exit_code == EXIT_OK
    assert json.loads(json_result.output) == []


def test_cli_check_runs_rules_by_target_kind_and_reports_findings(tmp_path: Path, monkeypatch) -> None:
    class ConfigOnlyRule(Rule):
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

    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    write_file(tmp_path / ".agent/tasks/fix.md", "---\ntype: task\n---\n# Task\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "load_rules", lambda: [ConfigOnlyRule()])

    result = runner.invoke(app, ["check", "--format", "json"], catch_exceptions=False)

    assert result.exit_code == EXIT_FINDINGS
    payload = json.loads(result.output)
    assert [finding["file"] for finding in payload] == ["AGENTS.md"]


def test_cli_check_keeps_list_targets_compatibility(tmp_path: Path, monkeypatch) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    write_file(tmp_path / ".agent/tasks/fix.md", "---\ntype: task\n---\n# Task\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "--list-targets"], catch_exceptions=False)

    assert result.exit_code == EXIT_OK
    assert result.output.splitlines() == [
        ".agent/tasks/fix.md\ttask",
        "AGENTS.md\tconfig",
    ]


def test_cli_usage_and_internal_errors_have_documented_exit_codes(monkeypatch) -> None:
    usage_result = runner.invoke(app, ["check", "--format", "xml"])
    assert usage_result.exit_code == EXIT_USAGE_ERROR

    def raise_internal_error(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "discover_targets", raise_internal_error)
    internal_result = runner.invoke(app, ["check"])

    assert internal_result.exit_code == EXIT_INTERNAL_ERROR
    assert "internal error: boom" in internal_result.stderr


def test_cli_explain_reads_existing_docs_and_handles_unknown_ids() -> None:
    existing_result = runner.invoke(app, ["explain", "KTL001"])
    unknown_result = runner.invoke(app, ["explain", "KTL999"])

    assert existing_result.exit_code == EXIT_OK
    assert "# KTL001: Context Bloat" in existing_result.output
    assert unknown_result.exit_code == EXIT_OK
    assert "KTL999 is 未実装/予約" in unknown_result.output


def test_cli_explain_falls_back_to_packaged_rule_docs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "_repo_rules_docs_dir", lambda: tmp_path)

    result = runner.invoke(app, ["explain", "KTL001"])

    assert result.exit_code == EXIT_OK
    assert "# KTL001: Context Bloat" in result.output
