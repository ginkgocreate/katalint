# KTL001: Context Bloat

## Summary

Persistent agent instruction files should stay concise enough for agents and
reviewers to understand. KTL001 reports files that exceed configured line or
byte limits.

## Category

config

## Default severity

warning

## Applies to

- AGENTS.md
- AGENTS.override.md
- CLAUDE.md
- .claude/agents/*.md

## Default thresholds

| Setting | Default |
| --- | --- |
| `max_lines` | 200 |
| `max_bytes` | 32768 |

## Rationale

Large persistent instruction files increase review cost and make it easier for
important guidance to be hidden below stale or task-specific content. Keeping
these files small encourages maintainers to move long procedures, examples, and
one-off task notes into more specific documents.

The byte threshold mirrors the default Codex project guidance cap documented
for AGENTS.md discovery. The line threshold follows Claude Code's documented
guidance to target concise CLAUDE.md files under 200 lines. Both references
were verified on 2026-07-07.

## Bad

```markdown
# AGENTS.md

## General

Always follow these rules.

## Historical migration notes

... 300 lines of old task notes ...
```

## Good

```markdown
# AGENTS.md

## Setup

- Install dependencies with `pnpm install`.
- Run tests with `pnpm test`.

## Working agreements

- Keep changes scoped to the requested task.
- Put long runbooks in `docs/runbooks/` and link them when needed.
```

## Detection

v0 counts physical lines and UTF-8 bytes. A finding is emitted when the line
count exceeds `max_lines` (strictly greater), or the byte size reaches or
exceeds `max_bytes` (greater than or equal). The byte check fires at the cap
because a file that has reached the 32 KiB budget is already at the limit of
Codex's combined instruction-chain allowance.

## Suggested remediation

- Move task-specific instructions to task packets.
- Move long operational procedures to runbooks or skills.
- Keep the root instruction file focused on stable repository norms.
- Split nested guidance into directory-local AGENTS.md or AGENTS.override.md
  files where supported.
