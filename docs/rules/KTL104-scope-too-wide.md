# KTL104: Scope Too Wide

## Summary
Flags task packets whose declared scope is too broad to plan, review, or
execute safely. A task should describe a bounded unit of work; when it points a
recursive glob at the tree, claims the whole repository in prose, or enumerates
a long list of files, it usually needs to be split.

## Category
workflow

## Default severity
warning

Unlike KTL101, KTL102, and KTL103 -- which default to `error` -- KTL104 defaults
to `warning`. As the "Default severity policy" section of `docs/rules/index.md`
notes, broad work can be intentional: a deliberately large refactor or sweep is
not always a mistake, so KTL104 nudges the author rather than blocking the task.

## Applies to
- Task packets (`type: task`) only. KTL104 does not run against handoff or
  config documents.

## Detection signals
- **Broad globs** -- recursive or root-level wildcards such as `src/**`,
  `app/**`, `**/*`, `**/`, or a bare `*.ext` at a directory root (e.g. `*.py`).
  A directory-scoped glob such as `src/*.py` does NOT trip this signal.
- **Repo-wide wording** -- phrases that claim the whole repository, for example
  "entire codebase", "the whole repo", "whole repository", "all files",
  "everything", "repo-wide", or the Japanese "全体", "すべてのファイル",
  "全ファイル".
- **Too many files** -- enumerating more than 5 distinct file paths in a single
  task.

## Rationale
Wide scope defeats the purpose of a task packet. Recursive globs and repo-wide
wording make it impossible to tell what "done" means, hide the true blast
radius of a change, and make review unreliable. Capping the number of named
files keeps each task small enough to reason about and to verify. Because a
broad sweep is sometimes exactly what is intended, this rule is a warning, not
an error.

## Bad
```markdown
---
type: task
---

# Modernize logging

Update modules under `src/**` to use the structured logging format introduced
last quarter.
```

## Good
```markdown
---
type: task
---

# Add password reset flow

Implement a password reset flow, scoped to:

- `src/auth/login.py`
- `src/auth/validators.py`
- `tests/auth/test_login.py`
```

## Detection
KTL104 is purely deterministic: it scans the raw task text with regular
expressions and simple token counting, with no semantic understanding of the
task. Backtick and tilde fenced code blocks, along with URLs, are stripped
before counting file paths, so example command output and links are never
mistaken for scope. A file is counted at most once (deduplicated by its literal
matched string), and the rule emits at most one finding per file that lists
every signal that tripped.

## Suggested remediation
- Split the task into smaller task packets, each with a single focused goal.
- Name a bounded set of files (5 or fewer) instead of a broad glob.
- Replace repo-wide wording with the specific paths you actually intend to
  change.
