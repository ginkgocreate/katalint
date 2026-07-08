from __future__ import annotations

from pathlib import Path

from katalint.rules.missing_handoff import MissingHandoffFieldsRule

FIXTURES = Path(__file__).parent.parent / "fixtures" / "workflow" / "missing_handoff"


def test_good_fixture_has_no_findings():
    rule = MissingHandoffFieldsRule()

    assert rule.check(FIXTURES / "good.md") == []


def test_bad_fixture_missing_exactly_two_fields():
    rule = MissingHandoffFieldsRule()

    findings = rule.check(FIXTURES / "bad.md")

    assert len(findings) == 2
    assert any("Test Results" in finding.message for finding in findings)
    assert any("Remaining Risks" in finding.message for finding in findings)


def test_bad_fixture_finding_attributes():
    rule = MissingHandoffFieldsRule()

    findings = rule.check(FIXTURES / "bad.md")

    assert findings, "expected findings for the incomplete handoff fixture"
    for finding in findings:
        assert finding.severity == "error"
        assert finding.rule_id == "KTL103"
        assert finding.category == "workflow"


def test_japanese_only_aliases_pass(tmp_path):
    rule = MissingHandoffFieldsRule()
    content = (
        "---\n"
        "type: handoff\n"
        "---\n\n"
        "# 引き継ぎ: 設定ローダー修正\n\n"
        "## 変更ファイル\n\n"
        "- src/katalint/config.py\n"
        "- src/katalint/cli.py\n\n"
        "## 実行コマンド\n\n"
        "`pytest`\n\n"
        "## テスト結果\n\n"
        "すべてのテストが成功しました。\n\n"
        "## 残リスク\n\n"
        "Windows のパス処理は未確認です。\n\n"
        "## 次のアクション\n\n"
        "レビューを依頼してください。\n"
    )
    path = tmp_path / "handoff_ja.md"
    path.write_text(content, encoding="utf-8")

    assert rule.check(path) == []


def test_applies_to():
    rule = MissingHandoffFieldsRule()

    assert rule.applies_to("handoff") is True
    assert rule.applies_to("task") is False
    assert rule.applies_to("config") is False
    assert rule.applies_to("unknown") is False


def test_unreadable_path_returns_empty(tmp_path):
    rule = MissingHandoffFieldsRule()

    missing = tmp_path / "does_not_exist.md"
    assert rule.check(missing) == []


def test_heading_inside_code_fence_does_not_count(tmp_path):
    rule = MissingHandoffFieldsRule()
    content = (
        "---\n"
        "type: handoff\n"
        "---\n\n"
        "# Handoff\n\n"
        "## Commands Run\n\n"
        "## Test Results\n\n"
        "## Remaining Risks\n\n"
        "## Next Action\n\n"
        "Here is an example of the section you should add:\n\n"
        "```markdown\n"
        "## Changed Files\n\n"
        "- src/foo.py\n"
        "```\n"
    )
    path = tmp_path / "fenced.md"
    path.write_text(content, encoding="utf-8")

    findings = rule.check(path)

    # The only genuinely missing field is Changed Files -- the fenced example
    # of that heading must NOT satisfy the requirement.
    assert len(findings) == 1
    assert "Changed Files" in findings[0].message


def test_tilde_code_fence_headings_ignored(tmp_path):
    rule = MissingHandoffFieldsRule()
    content = (
        "---\n"
        "type: handoff\n"
        "---\n\n"
        "# Handoff\n\n"
        "~~~\n"
        "## Changed Files\n"
        "## Commands Run\n"
        "## Test Results\n"
        "## Remaining Risks\n"
        "## Next Action\n"
        "~~~\n"
    )
    path = tmp_path / "tilde.md"
    path.write_text(content, encoding="utf-8")

    # Every field heading is inside the fence, so all 5 remain missing.
    assert len(rule.check(path)) == 5


def test_closing_atx_hashes_are_stripped(tmp_path):
    rule = MissingHandoffFieldsRule()
    content = (
        "---\n"
        "type: handoff\n"
        "---\n\n"
        "# Handoff\n\n"
        "## Changed Files ##\n\n"
        "## Commands Run ##\n\n"
        "## Test Results ##\n\n"
        "## Remaining Risks ##\n\n"
        "## Next Action ##\n"
    )
    path = tmp_path / "closing.md"
    path.write_text(content, encoding="utf-8")

    # Closing ATX hashes must not prevent a heading from matching its alias.
    assert rule.check(path) == []


def test_missing_all_fields(tmp_path):
    rule = MissingHandoffFieldsRule()
    content = (
        "---\n"
        "type: handoff\n"
        "---\n\n"
        "# Handoff title only\n\n"
        "Some prose but no required sections.\n"
    )
    path = tmp_path / "empty_handoff.md"
    path.write_text(content, encoding="utf-8")

    findings = rule.check(path)

    assert len(findings) == 5
