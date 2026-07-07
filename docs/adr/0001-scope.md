# ADR-0001: katalint scope

## Status

Accepted.

## Context

AI coding agents use repository-local and user-local instruction files to
shape coding behavior. These files are useful, but they can also become large,
stale, vague, or overloaded with rules that are better handled by deterministic
tools.

katalint needs a narrow first scope so it can be trusted as a CI linter instead
of drifting into an agent runner, prompt generator, or workflow orchestrator.

## Decision

katalint is a deterministic linter for AI coding agent instructions and
workflow documents.

The public interface is one linter command, `katalint check`. Rule families are
internal implementation concepts, not separate products or modes.

## In scope

- AGENTS.md
- AGENTS.override.md
- CLAUDE.md
- .claude/agents/*.md
- task packets
- handoff documents
- CI-friendly checks
- rule explanations
- JSON output
- text output

## Out of scope

- Running Codex
- Running Claude Code
- Calling LLMs by default
- Network-dependent checks
- Prompt orchestration
- Model routing
- Long-term memory
- Knowledge base management
- IDE integration in v0
- Autofix in v0

## Rule families

katalint checks two families of smells:

1. Configuration smells in persistent agent instruction files
2. Workflow smells in task packets and handoff documents

Configuration smells are the trust entry point because they align with existing
AGENTS.md and CLAUDE.md smell research. Workflow smells are the differentiator
because they cover the operational documents that make repeated agent work
reliable.

## v0 active rules

| Rule | Family | Name | Default severity |
| --- | --- | --- | --- |
| KTL001 | config | Context Bloat | warning |
| KTL002 | config | Lint Leakage | warning |
| KTL003 | config | Blind References | warning |
| KTL004 | config | Init Fossilization | warning |
| KTL101 | workflow | Missing Acceptance Criteria | error |
| KTL102 | workflow | Missing Verification Command | error |
| KTL103 | workflow | Missing Handoff Fields | error |
| KTL104 | workflow | Scope Too Wide | warning |

## Reserved rules

| Rule | Family | Name | Reason |
| --- | --- | --- | --- |
| KTL005 | config | Skill Leakage | Deferred until semantic checks can be designed conservatively |
| KTL006 | config | Conflicting Instructions | Deferred until semantic checks can be designed conservatively |
| KTL105 | workflow | Judgment / Execution Mixed | Deferred until semantic checks can be designed conservatively |

## Consequences

- katalint can run in CI without secrets, network access, model calls, or agent
  execution.
- v0 favors deterministic heuristics over broad semantic claims.
- Rules should provide explanations and suggestions before any fix command is
  considered.
- The first implementation PRs should not add scaffold generation, orchestration,
  or runtime features.

## Follow-up PRs

- PR-1: CLI skeleton and file discovery
- PR-2: rule engine, reporter, and exit codes
- PR-3: deterministic configuration-smell rules
- PR-4: deterministic workflow-smell rules
- PR-5: configuration, suppressions, and baseline
- PR-6: CI integration, dogfooding, and examples
- PR-7+: optional scaffold commands
