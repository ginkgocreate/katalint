"""PR-1.1: discovery classification adjustments + robustness regressions.

Covers:
- explicit-path config classification by basename at any depth (unblocks config
  rules such as KTL001-004 from being run against an explicitly passed file), and
- five robustness fixes in discovery (BOM, unreadable files, empty explicit list,
  unterminated frontmatter, out-of-root candidates).
"""

from pathlib import Path

from katalint.discovery import discover_targets


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def kinds(targets):
    return {t.path.as_posix(): t.kind for t in targets}


# --- explicit-path config classification (the KTL config-rule CLI unblock) ---

def test_explicit_deep_config_file_is_classified_config(tmp_path: Path) -> None:
    deep = tmp_path / "packages" / "app" / "AGENTS.md"
    write_file(deep, "# Agents\n")

    targets = discover_targets(paths=[deep], root=tmp_path)

    assert kinds(targets) == {"packages/app/AGENTS.md": "config"}


def test_explicit_directory_surfaces_nested_config_as_config(tmp_path: Path) -> None:
    write_file(tmp_path / "sub" / "CLAUDE.md", "# Claude\n")
    write_file(tmp_path / "sub" / "notes.md", "# Notes\n")

    targets = discover_targets(paths=[tmp_path / "sub"], root=tmp_path)

    assert kinds(targets) == {"sub/CLAUDE.md": "config", "sub/notes.md": "unknown"}


def test_nested_claude_agents_file_is_config(tmp_path: Path) -> None:
    nested = tmp_path / "pkg" / ".claude" / "agents" / "reviewer.md"
    write_file(nested, "---\nname: reviewer\n---\n")

    targets = discover_targets(paths=[nested], root=tmp_path)

    assert kinds(targets) == {"pkg/.claude/agents/reviewer.md": "config"}


def test_deeper_file_under_claude_agents_is_not_config(tmp_path: Path) -> None:
    # Only direct `.md` children of `.claude/agents` are subagent definitions;
    # files in deeper subdirectories are not (matches the `*.md` glob).
    deeper = tmp_path / ".claude" / "agents" / "sub" / "reviewer.md"
    write_file(deeper, "---\nname: reviewer\n---\n")

    assert kinds(discover_targets(paths=[deeper], root=tmp_path)) == {
        ".claude/agents/sub/reviewer.md": "unknown"
    }


def test_frontmatter_type_wins_over_config_basename(tmp_path: Path) -> None:
    # A workflow document named like a config file must still be a task/handoff
    # when it declares `type:` frontmatter — the basename must not shadow it.
    task = tmp_path / "docs" / "agent" / "tasks" / "AGENTS.md"
    write_file(task, "---\ntype: task\n---\n# Task\n")
    handoff = tmp_path / ".agent" / "handoffs" / "CLAUDE.md"
    write_file(handoff, "---\ntype: handoff\n---\n# Handoff\n")

    targets = discover_targets(paths=[task, handoff], root=tmp_path)

    assert kinds(targets) == {
        "docs/agent/tasks/AGENTS.md": "task",
        ".agent/handoffs/CLAUDE.md": "handoff",
    }


def test_config_basename_without_frontmatter_is_config(tmp_path: Path) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    assert kinds(discover_targets(paths=[tmp_path / "AGENTS.md"], root=tmp_path)) == {
        "AGENTS.md": "config"
    }


def test_frontmatter_does_not_turn_a_config_file_into_workflow(tmp_path: Path) -> None:
    # A genuine config file (config basename, not under a workflow dir) stays
    # config even if it carries a stray `type:` frontmatter.
    root_cfg = tmp_path / "AGENTS.md"
    write_file(root_cfg, "---\ntype: task\n---\n# Agents\n")

    assert kinds(discover_targets(paths=[root_cfg], root=tmp_path)) == {"AGENTS.md": "config"}


def test_config_basename_inside_workflow_dir_is_not_config(tmp_path: Path) -> None:
    # A config-named file with no frontmatter under a workflow directory keeps
    # PR-1's behaviour (unknown) rather than being reclassified as config.
    under_tasks = tmp_path / "docs" / "agent" / "tasks" / "AGENTS.md"
    write_file(under_tasks, "# not really a config\n")

    assert kinds(discover_targets(paths=[under_tasks], root=tmp_path)) == {
        "docs/agent/tasks/AGENTS.md": "unknown"
    }


# --- robustness regressions (five discovery fixes) ---

def test_utf8_bom_frontmatter_is_still_read(tmp_path: Path) -> None:
    path = tmp_path / "task.md"
    path.write_bytes("﻿---\ntype: task\n---\n# Task\n".encode("utf-8"))

    targets = discover_targets(paths=[path], root=tmp_path)

    assert kinds(targets) == {"task.md": "task"}


def test_unreadable_candidate_does_not_abort_discovery(tmp_path: Path) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")
    missing = tmp_path / "gone.md"  # referenced but does not exist

    # A candidate that cannot be read must not raise or drop the whole run.
    targets = discover_targets(paths=[tmp_path / "AGENTS.md", missing], root=tmp_path)

    assert kinds(targets) == {"AGENTS.md": "config"}


def test_empty_explicit_paths_yields_no_targets(tmp_path: Path) -> None:
    write_file(tmp_path / "AGENTS.md", "# Agents\n")

    # An explicit empty list means "no paths", not "fall back to default scan".
    assert discover_targets(paths=[], root=tmp_path) == []


def test_unterminated_frontmatter_does_not_classify(tmp_path: Path) -> None:
    path = tmp_path / ".agent" / "tasks" / "x.md"
    write_file(path, "---\n# no closing fence\n\ntype: task\n")

    targets = discover_targets(paths=[path], root=tmp_path)

    assert kinds(targets) == {".agent/tasks/x.md": "unknown"}


def test_out_of_root_explicit_file_is_skipped(tmp_path: Path) -> None:
    outside = tmp_path / "build" / "AGENTS.md"
    write_file(outside, "# Agents\n")
    root = tmp_path / "repo"
    root.mkdir()

    # A file outside the root is skipped cleanly (not returned with an absolute
    # path that would corrupt ignore/classification/sort).
    assert discover_targets(paths=[outside], root=root) == []
