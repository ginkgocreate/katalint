from __future__ import annotations

from pathlib import Path

from katalint.rules.prohibition_overload import ProhibitionOverloadRule

FIXTURES = Path(__file__).parent.parent / "fixtures" / "config" / "prohibition_overload"


def test_good_fixture_has_no_findings() -> None:
    rule = ProhibitionOverloadRule()
    findings = rule.check(FIXTURES / "good" / "AGENTS.md")
    assert findings == []


def test_bad_fixture_has_one_finding() -> None:
    rule = ProhibitionOverloadRule()
    findings = rule.check(FIXTURES / "bad" / "AGENTS.md")
    assert len(findings) == 1
    assert findings[0].rule_id == "KTL004"


def test_many_prohibitions_few_must_do_fires(tmp_path: Path) -> None:
    # 8 prohibition markers ("NEVER"), 0 must-do markers.
    file = tmp_path / "x.md"
    file.write_text("NEVER skip validation. " * 8, encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert len(findings) == 1
    assert findings[0].rule_id == "KTL004"


def test_many_prohibitions_many_must_do_no_finding(tmp_path: Path) -> None:
    # 8 prohibition markers ("NEVER") + 8 must-do markers ("ALWAYS"):
    # must_do_ratio = 8 / (8 + 8) = 0.50, so the strict ratio gate does not fire.
    file = tmp_path / "x.md"
    file.write_text(("NEVER skip. " * 8) + ("ALWAYS review. " * 8), encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert findings == []


def test_few_prohibitions_no_finding(tmp_path: Path) -> None:
    # Exactly 5 prohibition markers ("NEVER"), 0 must-do markers -> count gate not exceeded.
    file = tmp_path / "x.md"
    file.write_text("NEVER. " * 5, encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert findings == []


def test_prohibition_count_boundary(tmp_path: Path) -> None:
    rule = ProhibitionOverloadRule()

    # Exactly 5 prohibition markers ("NEVER"), 0 must-do: 5 is not > 5 -> no finding.
    five = tmp_path / "five.md"
    five.write_text("NEVER. " * 5, encoding="utf-8")
    assert rule.check(five) == []

    # Exactly 6 prohibition markers ("NEVER"), 0 must-do: 6 > 5 and ratio 0.00 < 0.5 -> fires.
    six = tmp_path / "six.md"
    six.write_text("NEVER. " * 6, encoding="utf-8")
    findings = rule.check(six)

    assert len(findings) == 1
    assert findings[0].rule_id == "KTL004"


def test_do_not_not_double_counted(tmp_path: Path) -> None:
    # 6 occurrences of "Do not skip validation." -> prohibition_count 6 (via "DO NOT"),
    # and must_do_count 0 because each "DO" match is excluded for heading a "DO NOT" phrase.
    file = tmp_path / "x.md"
    file.write_text("Do not skip validation. " * 6, encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "KTL004"
    assert "6 prohibitions" in finding.message
    assert "0 must-do" in finding.message


def test_ratio_zero_denominator_no_finding(tmp_path: Path) -> None:
    # No prohibition markers and no must-do markers at all.
    file = tmp_path / "x.md"
    file.write_text(
        "This plain prose describes project background and goals.", encoding="utf-8"
    )

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert findings == []


def test_unreadable_file_returns_empty(tmp_path: Path) -> None:
    rule = ProhibitionOverloadRule()
    findings = rule.check(tmp_path / "does_not_exist.md")
    assert findings == []


def test_applies_to_config_only() -> None:
    rule = ProhibitionOverloadRule()
    assert rule.applies_to("config") is True
    assert rule.applies_to("task") is False
    assert rule.applies_to("handoff") is False
    assert rule.applies_to("unknown") is False


def test_must_not_not_double_counted(tmp_path: Path) -> None:
    # 6 occurrences of "Must not skip." -> prohibition_count 6 (via "MUST NOT"),
    # must_do_count 0 because each "MUST" match is excluded for heading a "MUST NOT" phrase.
    file = tmp_path / "x.md"
    file.write_text("Must not skip. " * 6, encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "KTL004"
    assert "6 prohibitions" in finding.message
    assert "0 must-do" in finding.message


def test_standalone_must_counts_as_must_do(tmp_path: Path) -> None:
    # 10 occurrences of "You MUST do X." -> prohibition_count 0, so 0 is not > 5 -> no finding.
    # (Each line has a standalone "MUST" (not "must not") and a "do" (not "do not").)
    file = tmp_path / "x.md"
    file.write_text("You MUST do X. " * 10, encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert findings == []


def test_must_notify_not_matched_as_prohibition(tmp_path: Path) -> None:
    # Word-boundary matching: "must notify" must NOT match the "MUST NOT" prohibition;
    # it is a positive must-do. 6 must-do markers ("MUST"), 0 prohibitions -> no finding.
    file = tmp_path / "x.md"
    file.write_text("You must notify owners. " * 6, encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert findings == []


def test_do_notify_not_matched_as_prohibition(tmp_path: Path) -> None:
    # "do notify" must NOT match the "DO NOT" prohibition; it is a positive must-do.
    # 6 must-do markers ("DO"), 0 prohibitions -> no finding.
    file = tmp_path / "x.md"
    file.write_text("Do notify reviewers. " * 6, encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert findings == []


def test_real_must_not_still_fires(tmp_path: Path) -> None:
    # Real "You MUST NOT skip." x6 -> 6 prohibitions, 0 must-do -> still fires.
    file = tmp_path / "x.md"
    file.write_text("You MUST NOT skip. " * 6, encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert len(findings) == 1
    assert "6 prohibitions" in findings[0].message
    assert "0 must-do" in findings[0].message


def test_marker_embedded_in_word_not_matched(tmp_path: Path) -> None:
    # "mustard", "shoulder", "document", "nevertheless" embed marker text but are not
    # whole-word markers, so nothing matches -> no finding.
    file = tmp_path / "x.md"
    file.write_text("mustard shoulder document nevertheless " * 6, encoding="utf-8")

    rule = ProhibitionOverloadRule()
    findings = rule.check(file)

    assert findings == []
