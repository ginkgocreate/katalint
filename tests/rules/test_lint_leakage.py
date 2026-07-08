from __future__ import annotations

from pathlib import Path

from katalint.rules.lint_leakage import LintLeakageRule

FIXTURES = Path(__file__).parent.parent / "fixtures" / "config" / "lint_leakage"


def _rule() -> LintLeakageRule:
    return LintLeakageRule()


def test_prescriptive_rules_with_config_present(tmp_path):
    bad_text = (FIXTURES / "bad" / "AGENTS.md").read_text(encoding="utf-8")
    agents = tmp_path / "AGENTS.md"
    agents.write_text(bad_text, encoding="utf-8")
    (tmp_path / ".prettierrc").write_text("{}\n", encoding="utf-8")

    findings = _rule().check(agents)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "KTL002"
    assert finding.category == "config"
    assert finding.severity == "warning"
    assert finding.file == agents.as_posix()
    assert finding.line == 1
    assert "line length" in finding.message
    assert "trailing whitespace" in finding.message
    assert "found .prettierrc" in finding.message


def test_delegation_pattern_with_config_present_does_not_fire(tmp_path):
    good_text = (FIXTURES / "good" / "AGENTS.md").read_text(encoding="utf-8")
    agents = tmp_path / "AGENTS.md"
    agents.write_text(good_text, encoding="utf-8")
    (tmp_path / "ruff.toml").write_text("", encoding="utf-8")

    assert _rule().check(agents) == []


def test_good_fixture_alone_no_config():
    assert _rule().check(FIXTURES / "good" / "AGENTS.md") == []


def test_config_present_but_no_prescriptive_directive(tmp_path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "# Notes\n\nBe clear and concise; ask questions when unsure.\n",
        encoding="utf-8",
    )
    (tmp_path / ".prettierrc").write_text("{}\n", encoding="utf-8")

    assert _rule().check(agents) == []


def test_missing_file_returns_empty(tmp_path):
    assert _rule().check(tmp_path / "does_not_exist.md") == []


def test_applies_to():
    rule = _rule()
    assert rule.applies_to("config") is True
    assert rule.applies_to("task") is False
    assert rule.applies_to("handoff") is False
    assert rule.applies_to("unknown") is False


def test_ops_char_constraint_with_config_does_not_fire(tmp_path):
    # A non-style operational constraint that mentions a bare character count
    # (no line-length context) must NOT be mistaken for a line-length directive.
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "# Notes\n\nKeep PR summaries under 500 characters.\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")

    assert _rule().check(agents) == []


def test_line_length_directive_with_config_fires(tmp_path):
    # A real line-length rule ("lines under 80 characters") HAS line context and
    # must fire when a config file is present alongside it.
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "# Style\n\nKeep lines under 80 characters.\n",
        encoding="utf-8",
    )
    (tmp_path / ".prettierrc").write_text("{}\n", encoding="utf-8")

    findings = _rule().check(agents)

    assert len(findings) == 1
    assert findings[0].rule_id == "KTL002"
    assert "line length" in findings[0].message


def test_bad_fixture_alone_no_sibling_config():
    assert _rule().check(FIXTURES / "bad" / "AGENTS.md") == []
