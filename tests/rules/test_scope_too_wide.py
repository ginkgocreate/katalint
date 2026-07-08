from __future__ import annotations

from pathlib import Path

from katalint.rules.scope_too_wide import ScopeTooWideRule

FIXTURES = Path(__file__).parent.parent / "fixtures" / "workflow" / "scope_too_wide"


def _write_task(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "task.md"
    path.write_text("---\ntype: task\n---\n\n" + body, encoding="utf-8")
    return path


def test_good_fixture_has_no_findings():
    rule = ScopeTooWideRule()
    assert rule.check(FIXTURES / "good.md") == []


def test_bad_fixture_has_one_finding():
    rule = ScopeTooWideRule()
    findings = rule.check(FIXTURES / "bad.md")
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "KTL104"
    assert finding.severity == "warning"
    assert finding.category == "workflow"


def test_broad_glob_triggers(tmp_path):
    rule = ScopeTooWideRule()
    path = _write_task(
        tmp_path,
        "# Task\n\nRefactor the modules under `src/**` to use the new logger.\n",
    )
    findings = rule.check(path)
    assert len(findings) == 1
    assert "broad glob" in findings[0].message


def test_markdown_bold_is_not_a_broad_glob(tmp_path):
    # Regression: `**bold**` spans must NOT be treated as a broad glob.
    rule = ScopeTooWideRule()
    path = _write_task(
        tmp_path,
        "# Task\n\nKeep **existing behavior** intact while touching "
        "`src/logger.py`.\n",
    )
    assert rule.check(path) == []


def test_path_glob_still_triggers(tmp_path):
    rule = ScopeTooWideRule()
    for body in ("# Task\n\nRefactor src/**\n", "# Task\n\ntouch **/*.py\n"):
        findings = rule.check(_write_task(tmp_path, body))
        assert len(findings) == 1
        assert "broad glob" in findings[0].message


def test_paired_extensions_counted_distinctly(tmp_path):
    # Regression: `.tsx` must not collapse into `.ts`; six paired-extension
    # files must count as six and trip the >5 gate.
    rule = ScopeTooWideRule()
    path = _write_task(
        tmp_path,
        "# Task\n\nUpdate:\n\n"
        "- `app.ts`\n- `app.tsx`\n- `view.js`\n"
        "- `view.jsx`\n- `main.c`\n- `main.cpp`\n",
    )
    findings = rule.check(path)
    assert len(findings) == 1
    assert "6 files" in findings[0].message


def test_repo_wide_wording_triggers(tmp_path):
    rule = ScopeTooWideRule()
    path = _write_task(
        tmp_path,
        "# Task\n\nReview the entire codebase for logging calls in "
        "`src/logger.py` and `src/config.py`.\n",
    )
    findings = rule.check(path)
    assert len(findings) == 1
    assert "repo-wide wording" in findings[0].message


def test_japanese_repo_wide_wording_triggers(tmp_path):
    rule = ScopeTooWideRule()
    path = _write_task(
        tmp_path,
        "# Task\n\nすべてのファイル を確認してください。\n",
    )
    findings = rule.check(path)
    assert len(findings) == 1


def test_six_distinct_files_triggers(tmp_path):
    rule = ScopeTooWideRule()
    path = _write_task(
        tmp_path,
        "# Task\n\nUpdate the following modules:\n\n"
        "- `src/a.py`\n- `src/b.py`\n- `src/c.py`\n"
        "- `src/d.py`\n- `src/e.py`\n- `src/f.py`\n",
    )
    findings = rule.check(path)
    assert len(findings) == 1
    assert "6 files" in findings[0].message


def test_five_files_boundary_no_finding(tmp_path):
    rule = ScopeTooWideRule()
    path = _write_task(
        tmp_path,
        "# Task\n\nUpdate the following modules:\n\n"
        "- `src/a.py`\n- `src/b.py`\n- `src/c.py`\n"
        "- `src/d.py`\n- `src/e.py`\n",
    )
    assert rule.check(path) == []


def test_urls_not_counted_as_files(tmp_path):
    rule = ScopeTooWideRule()
    path = _write_task(
        tmp_path,
        "# Task\n\nSee https://example.com/a/b/c/d/e/f/g for details, then "
        "update `src/a.py` and `src/b.py`.\n",
    )
    assert rule.check(path) == []


def test_fenced_code_block_tokens_not_counted(tmp_path):
    rule = ScopeTooWideRule()
    body = (
        "# Task\n\nExample output:\n\n"
        "```\n"
        "a/b/c\nd/e/f\ng/h/i\nj/k/l\nm/n/o\np/q/r\ns/t/u\n"
        "```\n\n"
        "Update `src/a.py` and `src/b.py`.\n"
    )
    path = _write_task(tmp_path, body)
    assert rule.check(path) == []


def test_applies_to_task_only():
    rule = ScopeTooWideRule()
    assert rule.applies_to("task") is True
    assert rule.applies_to("handoff") is False
    assert rule.applies_to("config") is False


def test_unreadable_file_returns_empty(tmp_path):
    rule = ScopeTooWideRule()
    missing = tmp_path / "missing.md"
    assert rule.check(missing) == []
