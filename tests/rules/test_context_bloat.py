from __future__ import annotations

from pathlib import Path

from katalint.rules.context_bloat import ContextBloatRule

# tests/rules/ -> parent.parent is tests/ ; fixtures live under tests/fixtures/.
FIXTURES = Path(__file__).parent.parent / "fixtures" / "config" / "context_bloat"


def test_good_fixture_has_no_findings() -> None:
    rule = ContextBloatRule()

    findings = rule.check(FIXTURES / "good" / "AGENTS.md")

    assert findings == []


def test_bad_fixture_has_one_line_finding() -> None:
    rule = ContextBloatRule()

    findings = rule.check(FIXTURES / "bad" / "AGENTS.md")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "KTL001"
    # The bad fixture is over the line limit but well under the byte budget,
    # so the single finding must come from the LINE path.
    assert "lines" in finding.message
    assert "bytes" not in finding.message


def test_line_boundary(tmp_path: Path) -> None:
    rule = ContextBloatRule()

    exactly_200 = tmp_path / "exactly_200.md"
    exactly_200.write_text("line\n" * 200, encoding="utf-8")
    findings = rule.check(exactly_200)
    line_findings = [finding for finding in findings if "lines" in finding.message]
    assert line_findings == []  # 200 exactly => no line finding

    over_200 = tmp_path / "over_200.md"
    over_200.write_text("line\n" * 201, encoding="utf-8")
    findings = rule.check(over_200)
    line_findings = [finding for finding in findings if "lines" in finding.message]
    assert len(line_findings) == 1  # 201 => 1 line finding


def test_byte_boundary(tmp_path: Path) -> None:
    rule = ContextBloatRule()

    # Single long line => no line finding; only the byte rule is exercised.
    under_budget = tmp_path / "under_budget.md"
    under_budget.write_text("a" * 32767, encoding="utf-8")
    assert under_budget.stat().st_size == 32767
    findings = rule.check(under_budget)
    byte_findings = [finding for finding in findings if "bytes" in finding.message]
    assert byte_findings == []  # 32767 => no byte finding

    at_budget = tmp_path / "at_budget.md"
    at_budget.write_text("a" * 32768, encoding="utf-8")
    assert at_budget.stat().st_size == 32768
    findings = rule.check(at_budget)
    byte_findings = [finding for finding in findings if "bytes" in finding.message]
    assert len(byte_findings) == 1  # 32768 => 1 byte finding


def test_byte_finding_severity_is_warning(tmp_path: Path) -> None:
    rule = ContextBloatRule()
    at_budget = tmp_path / "at_budget.md"
    at_budget.write_text("a" * 32768, encoding="utf-8")

    findings = rule.check(at_budget)
    byte_findings = [finding for finding in findings if "bytes" in finding.message]

    assert byte_findings[0].severity == "warning"


def test_applies_to_config_only() -> None:
    rule = ContextBloatRule()

    assert rule.applies_to("config") is True
    assert rule.applies_to("task") is False
    assert rule.applies_to("handoff") is False
    assert rule.applies_to("unknown") is False
