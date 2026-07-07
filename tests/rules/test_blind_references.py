from __future__ import annotations

from pathlib import Path

from katalint.rules.blind_references import BlindReferencesRule

FIXTURES = Path(__file__).parent.parent / "fixtures" / "config" / "blind_references"


def test_vague_reference_without_anchor_is_flagged(tmp_path: Path) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "intro line\nfollow the existing pattern\ntrailing line\n",
        encoding="utf-8",
    )
    rule = BlindReferencesRule()
    findings = rule.check(target)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.line == 2
    assert finding.rule_id == "KTL003"
    assert finding.category == "config"
    assert finding.severity == "warning"


def test_vague_reference_with_url_on_same_line_has_no_finding(tmp_path: Path) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "see https://example.com/guide and follow the existing pattern\n",
        encoding="utf-8",
    )
    rule = BlindReferencesRule()
    findings = rule.check(target)
    assert findings == []


def test_vague_reference_with_path_on_adjacent_line_has_no_finding(
    tmp_path: Path,
) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "as before\nsee docs/style-guide.md for details\n",
        encoding="utf-8",
    )
    rule = BlindReferencesRule()
    findings = rule.check(target)
    assert findings == []


def test_vague_reference_with_section_reference_has_no_finding(tmp_path: Path) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "the current approach\nsee section 3 for details\n",
        encoding="utf-8",
    )
    rule = BlindReferencesRule()
    findings = rule.check(target)
    assert findings == []


def test_only_concrete_references_has_zero_findings(tmp_path: Path) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "Follow the existing pattern in docs/style.md.\n"
        "As before, see https://example.com/x.\n",
        encoding="utf-8",
    )
    rule = BlindReferencesRule()
    findings = rule.check(target)
    assert findings == []


def test_good_fixture_has_no_findings() -> None:
    rule = BlindReferencesRule()
    findings = rule.check(FIXTURES / "good" / "AGENTS.md")
    assert len(findings) == 0


def test_bad_fixture_has_at_least_one_finding() -> None:
    rule = BlindReferencesRule()
    findings = rule.check(FIXTURES / "bad" / "AGENTS.md")
    assert len(findings) >= 1
    assert all(finding.rule_id == "KTL003" for finding in findings)


def test_missing_file_returns_empty_list(tmp_path: Path) -> None:
    rule = BlindReferencesRule()
    findings = rule.check(tmp_path / "does-not-exist.md")
    assert findings == []


def test_applies_to_config_only() -> None:
    rule = BlindReferencesRule()
    assert rule.applies_to("config") is True
    assert rule.applies_to("task") is False
    assert rule.applies_to("handoff") is False
    assert rule.applies_to("unknown") is False
