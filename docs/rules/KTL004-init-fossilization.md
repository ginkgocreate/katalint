# KTL004: Init Fossilization

## Summary

Persistent agent instruction files should be maintained as the repository
changes. KTL004 reports AGENTS.md or CLAUDE.md files that appear to have been
created once and then left untouched while the rest of the repository continued
to evolve.

## Category

config

## Default severity

warning

## Applies to

- AGENTS.md
- CLAUDE.md

## Default thresholds

| Setting | Default |
| --- | --- |
| `max_file_commits` | 1 |
| `min_repo_commits` | 8 |

## Rationale

Agent instruction files are operational guidance, not one-time scaffolding. If
the repository has accumulated meaningful history but the instruction file has
only its initial commit, it is likely stale, generated, or no longer reviewed.

KTL004 is intentionally Git-based and deterministic. It does not judge the text
semantically; it only compares file maintenance history with repository
activity.

## Bad

```text
Repository history:
- AGENTS.md touched in 1 commit
- repository has 50 commits
```

## Good

```text
Repository history:
- AGENTS.md touched in 3 commits
- repository has 50 commits
```

## Detection

v0 emits one warning when all of these conditions are true:

- the file name is AGENTS.md or CLAUDE.md
- the file is tracked by Git
- the repository has at least `min_repo_commits` commits
- the file appears in `max_file_commits` or fewer commits

Files outside Git repositories, untracked files, and young repositories are
skipped.

## Suggested remediation

- Review the instruction file for stale generated content.
- Make a small maintenance update if the file is still useful.
- Remove or replace old guidance that no longer matches the repository.
