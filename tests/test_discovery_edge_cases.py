"""Edge-case regressions for discovery.py not covered by test_discovery.py /
test_discovery_classification.py.

Covers behaviour that discovery.py actually implements today:
- symlink handling (resolved-path classification, directory traversal,
  broken links, links that escape the scan root), pinned down because
  `discover_targets` resolves every candidate with `Path.resolve()` before
  classifying and relativizing it, which has non-obvious consequences;
- multi-level nesting under the `**` default patterns, and IGNORE_DIR_NAMES
  applying at any depth (including inside a workflow directory);
- case-sensitive basename/directory matching in `_is_config_path`, exercised
  directly against `classify_target` so the assertions do not depend on the
  host filesystem's case (in)sensitivity.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

from katalint.discovery import classify_target, discover_targets


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def kinds(targets):
    return {t.path.as_posix(): t.kind for t in targets}


skip_on_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="symlink creation needs elevated privileges on Windows",
)


# --- symlinks -----------------------------------------------------------


@skip_on_windows
def test_symlinked_config_file_is_classified_by_its_resolved_path(tmp_path: Path) -> None:
    # discover_targets() calls Path.resolve() on every candidate before
    # classifying/relativizing it, so a symlink named AGENTS.md that points at
    # a differently-named real file is classified (and reported) under the
    # *target's* path, not the "AGENTS.md" name used to discover it.
    real_file = tmp_path / "real" / "actual_agents.md"
    write_file(real_file, "# Agents\n")
    os.symlink(real_file, tmp_path / "AGENTS.md")

    targets = discover_targets(root=tmp_path)

    assert kinds(targets) == {"real/actual_agents.md": "unknown"}


@skip_on_windows
def test_default_discovery_traverses_symlinked_task_directory(tmp_path: Path) -> None:
    real_dir = tmp_path / "real_tasks"
    write_file(real_dir / "task1.md", "---\ntype: task\n---\n# Task\n")
    (tmp_path / ".agent").mkdir()
    os.symlink(real_dir, tmp_path / ".agent" / "tasks")

    targets = discover_targets(root=tmp_path)

    assert kinds(targets) == {"real_tasks/task1.md": "task"}


@skip_on_windows
def test_explicit_scan_of_a_symlinked_directory_itself_is_traversed(tmp_path: Path) -> None:
    real_dir = tmp_path / "real_tasks"
    write_file(real_dir / "task1.md", "---\ntype: task\n---\n# Task\n")
    (tmp_path / ".agent").mkdir()
    link = tmp_path / ".agent" / "tasks"
    os.symlink(real_dir, link)

    # The explicit path passed IS the symlink; rglob() follows a symlink that
    # is the traversal root (or an exact pattern segment), consistently
    # across Python versions.
    targets = discover_targets(paths=[link], root=tmp_path)

    assert kinds(targets) == {"real_tasks/task1.md": "task"}


@skip_on_windows
def test_explicit_scan_does_not_descend_into_a_symlinked_subdirectory(tmp_path: Path) -> None:
    # In contrast to the case above: rglob("*.md")'s "**" recursion does not
    # follow a symlink that it *encounters while walking* an explicitly
    # scanned real directory (only a symlink that is itself the search root
    # is followed). A symlinked subdirectory a couple of levels deep is
    # therefore silently skipped, consistently across Python versions
    # (verified on both 3.10, which has no `recurse_symlinks` pathlib
    # parameter, and 3.14, which defaults it to False).
    real_dir = tmp_path / "real_tasks"
    write_file(real_dir / "task1.md", "---\ntype: task\n---\n# Task\n")
    docs = tmp_path / "docs"
    docs.mkdir()
    os.symlink(real_dir, docs / "tasks")

    targets = discover_targets(paths=[docs], root=tmp_path)

    assert targets == []


@skip_on_windows
def test_broken_symlink_is_skipped_by_default_discovery(tmp_path: Path) -> None:
    os.symlink(tmp_path / "does-not-exist.md", tmp_path / "AGENTS.md")

    assert discover_targets(root=tmp_path) == []


@skip_on_windows
def test_broken_symlink_passed_explicitly_is_skipped(tmp_path: Path) -> None:
    broken = tmp_path / "AGENTS.md"
    os.symlink(tmp_path / "does-not-exist.md", broken)
    real = tmp_path / "CLAUDE.md"
    write_file(real, "# Claude\n")

    targets = discover_targets(paths=[broken, real], root=tmp_path)

    assert kinds(targets) == {"CLAUDE.md": "config"}


@skip_on_windows
def test_symlink_escaping_root_is_not_discovered(tmp_path: Path) -> None:
    # A candidate whose resolved, real path falls outside the scan root is
    # dropped (relative_to() raises ValueError and discover_targets skips
    # it) rather than being reported at an absolute or ".."-relative path.
    with tempfile.TemporaryDirectory() as outside:
        outside_file = Path(outside) / "AGENTS.md"
        write_file(outside_file, "# outside\n")
        os.symlink(outside_file, tmp_path / "AGENTS.md")

        assert discover_targets(root=tmp_path) == []


# --- nested directories ---------------------------------------------------


def test_deeply_nested_task_file_is_discovered_by_default_scan(tmp_path: Path) -> None:
    deep = tmp_path / ".agent" / "tasks" / "a" / "b" / "c" / "deep.md"
    write_file(deep, "---\ntype: task\n---\n# Deep\n")

    targets = discover_targets(root=tmp_path)

    assert kinds(targets) == {".agent/tasks/a/b/c/deep.md": "task"}


def test_ignored_dir_nested_inside_workflow_path_is_excluded_by_default_scan(
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / ".agent" / "tasks" / "vendor" / "x.md",
        "---\ntype: task\n---\n# X\n",
    )

    assert discover_targets(root=tmp_path) == []


def test_ignored_dir_nested_inside_workflow_path_is_excluded_by_explicit_scan(
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / ".agent" / "tasks" / "vendor" / "x.md",
        "---\ntype: task\n---\n# X\n",
    )

    assert discover_targets(paths=[tmp_path / ".agent" / "tasks"], root=tmp_path) == []


# --- case sensitivity -------------------------------------------------------
#
# Exercised directly against classify_target() with a relative_path that has
# no backing file on disk: the alternate-case names below aren't config
# matches, so classification falls straight through to
# _read_frontmatter_type(), which returns None for a non-existent path (an
# OSError it already swallows) without ever needing the file to exist. This
# keeps the assertions independent of the host filesystem's case folding
# (relevant on case-insensitive filesystems such as default macOS/Windows).


def test_config_basename_matching_is_case_sensitive() -> None:
    relative_path = Path("agents.md")
    absolute_path = Path("/nonexistent") / relative_path

    assert classify_target(absolute_path, relative_path) == "unknown"


def test_claude_agents_directory_matching_is_case_sensitive_on_dot_claude() -> None:
    relative_path = Path(".CLAUDE/agents/reviewer.md")
    absolute_path = Path("/nonexistent") / relative_path

    assert classify_target(absolute_path, relative_path) == "unknown"


def test_claude_agents_directory_matching_is_case_sensitive_on_agents(
) -> None:
    relative_path = Path(".claude/Agents/reviewer.md")
    absolute_path = Path("/nonexistent") / relative_path

    assert classify_target(absolute_path, relative_path) == "unknown"
