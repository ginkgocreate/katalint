# AGENTS.md

Purpose: guidance for coding agents working on katalint.

## Scope

- Build katalint as a deterministic CLI linter for agent instruction files,
  task packets, and handoff documents.
- Do not add agent execution, model calls, network-dependent checks, autofix,
  scaffold commands, or routing features unless the task explicitly asks for it.
- Keep changes narrow and aligned with the active rule catalogue in
  `docs/rules/index.md`.

## Workflow

- Add or update tests before changing behavior.
- Keep rule checks deterministic and safe for local development and CI.
- Expose rule settings only through `Rule.configurable_options`; invalid user
  configuration must produce a usage error rather than an internal error.
- Run the relevant test suite and `katalint check` before handoff.
- Record unresolved issues in `SCRATCHPAD.md` with a clear label and next step.

## Handoff

- Include changed files, commands run, test results, remaining risks, and the
  next action.
