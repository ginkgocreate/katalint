from __future__ import annotations

from pathlib import Path

import pytest

from katalint.rules.missing_acceptance import MissingAcceptanceCriteriaRule

FIXTURES = (
    Path(__file__).parent.parent / "fixtures" / "workflow" / "missing_acceptance"
)


def _write_task_with_heading(tmp_path: Path, heading: str) -> Path:
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Some Task\n"
        "\n"
        "Body text.\n"
        "\n"
        f"## {heading}\n"
        "\n"
        "- item\n",
        encoding="utf-8",
    )
    return file


def test_good_fixture_returns_no_findings() -> None:
    rule = MissingAcceptanceCriteriaRule()

    assert rule.check(FIXTURES / "good.md") == []


def test_bad_fixture_returns_single_error_finding() -> None:
    rule = MissingAcceptanceCriteriaRule()

    findings = rule.check(FIXTURES / "bad.md")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "KTL101"
    assert finding.severity == "error"


@pytest.mark.parametrize(
    "heading",
    [
        "Acceptance Criteria",
        "Done When",
        "Definition of Done",
        "完了条件",
        "受け入れ条件",
    ],
)
def test_each_accepted_heading_alias_is_recognized(
    tmp_path: Path, heading: str
) -> None:
    rule = MissingAcceptanceCriteriaRule()
    file = _write_task_with_heading(tmp_path, heading)

    assert rule.check(file) == []


def test_definition_of_done_alias_produces_zero_findings(tmp_path: Path) -> None:
    rule = MissingAcceptanceCriteriaRule()
    file = _write_task_with_heading(tmp_path, "Definition of Done")

    assert rule.check(file) == []


def test_ukeire_alias_produces_zero_findings(tmp_path: Path) -> None:
    rule = MissingAcceptanceCriteriaRule()
    file = _write_task_with_heading(tmp_path, "受け入れ条件")

    assert rule.check(file) == []


def test_heading_inside_fenced_code_block_does_not_suppress(tmp_path: Path) -> None:
    rule = MissingAcceptanceCriteriaRule()
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Some Task\n"
        "\n"
        "Example of what a section looks like:\n"
        "\n"
        "```\n"
        "## Acceptance Criteria\n"
        "\n"
        "- item\n"
        "```\n",
        encoding="utf-8",
    )

    findings = rule.check(file)

    assert len(findings) == 1
    assert findings[0].rule_id == "KTL101"
    assert findings[0].severity == "error"


def test_closing_hash_sequence_is_stripped(tmp_path: Path) -> None:
    rule = MissingAcceptanceCriteriaRule()
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Some Task\n"
        "\n"
        "## Acceptance Criteria ##\n"
        "\n"
        "- item\n",
        encoding="utf-8",
    )

    assert rule.check(file) == []


def test_applies_to_task_is_true() -> None:
    rule = MissingAcceptanceCriteriaRule()

    assert rule.applies_to("task") is True


def test_applies_to_handoff_is_false() -> None:
    rule = MissingAcceptanceCriteriaRule()

    assert rule.applies_to("handoff") is False


def test_applies_to_config_is_false() -> None:
    rule = MissingAcceptanceCriteriaRule()

    assert rule.applies_to("config") is False


def test_applies_to_unknown_is_false() -> None:
    rule = MissingAcceptanceCriteriaRule()

    assert rule.applies_to("unknown") is False


def test_unreadable_file_returns_empty_list(tmp_path: Path) -> None:
    rule = MissingAcceptanceCriteriaRule()
    missing = tmp_path / "does_not_exist.md"

    assert rule.check(missing) == []
