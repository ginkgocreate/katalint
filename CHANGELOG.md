# Changelog

All notable changes to katalint are documented here.

## 0.1.1 - 2026-07-19

First release published to PyPI. (The v0.1.0 GitHub release predated the
publish workflow, so its artifacts never reached PyPI.)

### Fixed

- Reject unknown rule IDs, internal rule attributes, and invalid numeric
  thresholds as configuration usage errors instead of ignoring them or
  crashing during a check.
- Ignore file paths inside both backtick and tilde fenced code examples when
  KTL104 counts the files named by a task packet.

## 0.1.0 - 2026-07-09

Initial public release.

### Added

- CLI entry point: `katalint check`, `katalint --version`, and
  `katalint explain <RULE_ID>`.
- Target discovery for AGENTS.md, AGENTS.override.md, CLAUDE.md, Claude Code
  subagents, task packets, and handoff documents.
- Configuration smells: KTL001 Context Bloat, KTL002 Lint Leakage, KTL003
  Blind References, and KTL004 Init Fossilization.
- Workflow smells: KTL101 Missing Acceptance Criteria, KTL102 Missing
  Verification Command, KTL103 Missing Handoff Fields, and KTL104 Scope Too
  Wide.
- Text and JSON output.
- `katalint.yml` support for targets, ignore paths, rule settings, severity
  overrides, `fail_on`, and baseline paths.
- Inline suppressions with required reasons.
- Baseline write/read support for incremental adoption.
- GitHub Actions and pre-commit examples.

### Design Boundaries

- No network access.
- No model calls.
- No agent execution.
- No workflow orchestration.
- No model routing.
