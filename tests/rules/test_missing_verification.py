from __future__ import annotations

from pathlib import Path

from katalint.rules.missing_verification import MissingVerificationRule

FIXTURES = Path(__file__).parent.parent / "fixtures" / "workflow" / "missing_verification"


def test_good_fixture_has_no_findings():
    rule = MissingVerificationRule()

    assert rule.check(FIXTURES / "good.md") == []


def test_bad_fixture_reports_one_finding():
    rule = MissingVerificationRule()

    findings = rule.check(FIXTURES / "bad.md")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "KTL102"
    assert finding.severity == "error"
    assert finding.category == "workflow"
    assert "bad.md" in finding.message
    assert "no verification command or section" in finding.message
    assert finding.suggestion


def test_command_vocabulary_without_verification_heading_has_no_findings(tmp_path):
    rule = MissingVerificationRule()
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Update the greeting copy\n"
        "\n"
        "Run `pytest -q` before submitting.\n",
        encoding="utf-8",
    )

    assert rule.check(file) == []


def test_verification_heading_without_command_vocabulary_has_no_findings(tmp_path):
    rule = MissingVerificationRule()
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Update the greeting copy\n"
        "\n"
        "## Verification\n"
        "\n"
        "Confirm the page renders and the copy reads well.\n",
        encoding="utf-8",
    )

    assert rule.check(file) == []


def test_generic_word_in_prose_heading_reports_finding(tmp_path):
    # "build" appears only as a prose word in the title, never as a runnable
    # command, and there is no verification section -> must be flagged.
    rule = MissingVerificationRule()
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Build the signup page\n"
        "\n"
        "Create the new signup page with the agreed layout and copy.\n",
        encoding="utf-8",
    )

    findings = rule.check(file)

    assert len(findings) == 1
    assert findings[0].rule_id == "KTL102"
    assert findings[0].severity == "error"


def test_generic_word_in_inline_code_has_no_findings(tmp_path):
    # A generic command word inside an inline code span IS a real command.
    rule = MissingVerificationRule()
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Ship the config change\n"
        "\n"
        "Run `tsc --noEmit` to confirm the types still check.\n",
        encoding="utf-8",
    )

    assert rule.check(file) == []


def test_command_in_fenced_code_block_has_no_findings(tmp_path):
    rule = MissingVerificationRule()
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Ship the config change\n"
        "\n"
        "```bash\n"
        "npm test\n"
        "```\n",
        encoding="utf-8",
    )

    assert rule.check(file) == []


def test_verification_heading_with_closing_hashes_has_no_findings(tmp_path):
    # Optional closing ATX hashes must not defeat the heading match.
    rule = MissingVerificationRule()
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Update the greeting copy\n"
        "\n"
        "## Verification ##\n"
        "\n"
        "Confirm the page renders and the copy reads well.\n",
        encoding="utf-8",
    )

    assert rule.check(file) == []


def test_verification_heading_inside_code_fence_is_ignored(tmp_path):
    # A `## Verification` that only appears inside a fenced code example must
    # NOT satisfy the section check, so this task is still flagged.
    rule = MissingVerificationRule()
    file = tmp_path / "task.md"
    file.write_text(
        "---\n"
        "type: task\n"
        "---\n"
        "\n"
        "# Document the packet format\n"
        "\n"
        "An example packet looks like:\n"
        "\n"
        "```markdown\n"
        "## Verification\n"
        "\n"
        "Describe how to check the work here.\n"
        "```\n"
        "\n"
        "Explain the fields above in prose.\n",
        encoding="utf-8",
    )

    findings = rule.check(file)

    assert len(findings) == 1
    assert findings[0].rule_id == "KTL102"


def test_rule_applies_to_task_only():
    rule = MissingVerificationRule()

    assert rule.applies_to("task") is True
    assert rule.applies_to("handoff") is False
    assert rule.applies_to("config") is False


def test_unreadable_file_returns_no_findings(tmp_path):
    rule = MissingVerificationRule()
    file = tmp_path / "does-not-exist.md"

    assert rule.check(file) == []
