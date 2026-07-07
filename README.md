# katalint

A fast, deterministic linter for AI coding agent instructions.

katalint checks AGENTS.md, CLAUDE.md, Claude Code subagents, task packets,
and handoff documents for configuration and workflow smells that make CLI
coding agents less reliable.

It does not run agents, call models, or orchestrate workflows. It only checks
the instructions you give to agents.

Status: PR-0 design scaffold. The CLI contract is documented here before the
implementation starts.

## What it is

katalint is a CI-friendly linter for the Markdown files and workflow documents
that shape AI coding agent behavior:

- AGENTS.md
- AGENTS.override.md
- CLAUDE.md
- .claude/agents/*.md
- task packets
- handoff documents

The public interface is intentionally one command:

```bash
katalint check
```

Internally, katalint checks two families of smells:

1. Configuration smells in persistent agent instruction files
2. Workflow smells in task packets and handoff documents

The split matters for implementation, but users should experience katalint as
one linter that reviews the instruction surface around their agents.

## What it is not

katalint is not:

- an agent runtime
- a Codex or Claude Code wrapper
- a prompt management framework
- a model router
- a knowledge base
- an orchestration system

v0 does not include:

- `katalint run`
- `katalint fix`
- LLM-based checks
- network access
- model calls
- agent execution
- workflow orchestration

## Why this exists

AI coding agents increasingly rely on persistent instruction files such as
AGENTS.md and CLAUDE.md. When these files become bloated, stale, conflicting,
or filled with low-value rules, agents waste context and become less reliable.

katalint helps maintainers keep these instructions reviewable, concise, and
operationally useful. It focuses on deterministic checks that are safe to run
locally, in pre-commit hooks, and in CI.

The configuration-smell rules are aligned with published research on
AGENTS.md and CLAUDE.md failure modes. The workflow-smell rules cover task
packets and handoff documents, where agent reliability often depends on clear
acceptance criteria, verification commands, and explicit next actions.

## Quick start

Target v0 CLI:

```bash
katalint check
katalint check AGENTS.md
katalint check .claude/agents/
katalint explain KTL001
```

Target CI contract:

```bash
katalint check --format text
katalint check --format json
```

## Example output

```text
AGENTS.md
  warning KTL001 config/context-bloat
  AGENTS.md has 236 lines. Recommended default is 200 lines or less.

docs/tasks/fix-parser.md
  error KTL101 workflow/missing-acceptance-criteria
  Task packet has no acceptance criteria section.

docs/handoff/2026-07-07.md
  error KTL103 workflow/missing-handoff-fields
  Missing required handoff fields: tests, risks, next_action.
```

## What katalint checks

katalint discovers these files by default:

- AGENTS.md
- AGENTS.override.md
- CLAUDE.md
- .claude/agents/*.md
- docs/tasks/**/*.md
- docs/handoff/**/*.md
- .katalint/tasks/**/*.md
- .katalint/handoff/**/*.md

Configuration checks look for persistent instruction-file smells such as
context bloat, lint leakage, vague references, and stale generated files.

Workflow checks look for task and handoff problems such as missing acceptance
criteria, missing verification commands, missing handoff fields, and overly
broad task scope.

## Rule catalogue

| Rule | Category | Description | Default |
| --- | --- | --- | --- |
| KTL001 | config | Context file is too large | warning |
| KTL002 | config | Instructions duplicate deterministic lint or format rules | warning |
| KTL003 | config | References are too vague or unresolved | warning |
| KTL004 | config | Agent config appears generated once and never maintained | warning |
| KTL101 | workflow | Task packet has no acceptance criteria | error |
| KTL102 | workflow | Task packet has no verification command | error |
| KTL103 | workflow | Handoff document misses required fields | error |
| KTL104 | workflow | Task scope appears too broad | warning |

Reserved rules:

| Rule | Category | Description | Reason reserved |
| --- | --- | --- | --- |
| KTL005 | config | Skill leakage | Needs semantic analysis to avoid noisy matches |
| KTL006 | config | Conflicting instructions | Needs semantic analysis to avoid noisy matches |
| KTL105 | workflow | Judgment and execution mixed | Needs semantic analysis to avoid noisy matches |

## Configuration

Target v0 configuration shape:

```yaml
version: 1
targets:
  agent_configs:
    - AGENTS.md
    - CLAUDE.md
    - .claude/agents/*.md
  task_packets:
    - docs/tasks/**/*.md
  handoffs:
    - docs/handoff/**/*.md
rules:
  KTL001:
    max_lines: 200
    max_bytes: 32768
    severity: warning
  KTL104:
    max_files_per_task: 5
    severity: warning
fail_on: error
ignore:
  - vendor/**
  - docs/archive/**
```

Configuration loading is out of scope for PR-0 and scheduled after the rule
engine exists.

## CI usage

Target GitHub Actions usage:

```yaml
name: katalint
on:
  pull_request:
  push:
    branches: [main]
jobs:
  katalint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uvx katalint check
```

CI integration is scheduled after the active v0 rules exist.

## Suppressions

Target inline suppression format:

```markdown
<!-- katalint-disable KTL002: project intentionally documents style because no formatter exists -->
```

Suppressions must include a reason. They are planned for the configuration and
baseline phase, not PR-0.

## Design principles

- Deterministic by default
- No network access
- No model calls
- No agent execution
- Fast enough for CI
- Conservative severity defaults
- Rule explanations before autofix
- One public linter interface, even though rules are grouped internally

## Roadmap

| Phase | PR | Outcome |
| --- | --- | --- |
| Phase 0 | PR-0 | README, ADR, and rule catalogue fix the scope |
| Phase 1 | PR-1 to PR-2 | CLI target discovery and finding/reporting foundation |
| Phase 2 | PR-3 | Deterministic configuration-smell rules |
| Phase 3 | PR-4 | Deterministic workflow-smell rules |
| Phase 4 | PR-5 to PR-6 | Configuration, suppressions, CI examples, and dogfooding |
| Phase 5 | PR-7+ | Optional scaffold commands and experimental features |

First public preview can happen after PR-4. A practical v0.1.0 should wait
until PR-6 so adoption, CI examples, and dogfooding are in place.

## References

- OpenAI Codex documents AGENTS.md discovery, layered guidance, and the default
  32 KiB project guidance cap:
  https://developers.openai.com/codex/guides/agents-md
- Claude Code documents CLAUDE.md memory behavior and recommends specific,
  concise instructions:
  https://docs.anthropic.com/en/docs/claude-code/memory
- Claude Code documents project and user subagents as Markdown files with YAML
  frontmatter:
  https://docs.anthropic.com/en/docs/claude-code/sub-agents
- "Configuration Smells in AGENTS.md Files" catalogues six configuration
  smells for AGENTS.md and CLAUDE.md files:
  https://arxiv.org/abs/2606.15828
