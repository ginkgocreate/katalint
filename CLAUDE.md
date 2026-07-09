# CLAUDE.md

Purpose: persistent Claude Code guidance for katalint.

## Working Rules

- Treat katalint as a linter, not as an agent runtime or prompt generator.
- Prefer small deterministic checks over semantic guesses.
- Keep CLI behavior compatible with the public contract in `README.md`.
- Use `docs/rules/index.md` and each `docs/rules/KTL*.md` page as rule anchors.
- Update tests and examples when changing CLI behavior, output shape, or rule
  configuration.

## Before Handoff

- Run the focused tests for the touched area.
- Run the full test suite when behavior crosses rule, discovery, reporter, or
  CLI boundaries.
- Run `katalint check` from the repository root.
- Note any unresolved question in `SCRATCHPAD.md`.
