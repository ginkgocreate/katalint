# katalint

A fast, deterministic linter for AI coding agent instructions.

katalint checks AGENTS.md, CLAUDE.md, Claude Code subagents, task packets,
and handoff documents for configuration and workflow smells that make CLI
coding agents less reliable.

It does not run agents, call models, or orchestrate workflows. It only checks
the instructions you give to agents.

Status: active v0 implementation. The CLI can discover targets, run the active
deterministic rules, load `katalint.yml`, apply inline suppressions, and use a
baseline file.

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

Basic CLI:

```bash
katalint check
katalint check AGENTS.md
katalint check .claude/agents/
katalint explain KTL001
```

CI-oriented output:

```bash
katalint check --format text
katalint check --format json
katalint check --write-baseline katalint-baseline.json
katalint check --baseline katalint-baseline.json
```

## Example output

```text
AGENTS.md
  warning KTL001 config/context-bloat
  AGENTS.md has 236 lines. Recommended default is 200 lines or less.

docs/agent/tasks/fix-parser.md
  error KTL101 workflow/missing-acceptance-criteria
  Task packet has no acceptance criteria section.

docs/agent/handoffs/2026-07-07.md
  error KTL103 workflow/missing-handoff-fields
  Missing required handoff fields: tests, risks, next_action.
```

## What katalint checks

katalint discovers these files by default:

- AGENTS.md
- AGENTS.override.md
- CLAUDE.md
- .claude/agents/*.md
- .agent/tasks/**/*.md
- docs/agent/tasks/**/*.md
- .agent/handoffs/**/*.md
- docs/agent/handoffs/**/*.md

The default ignore list is:

- vendor/**
- node_modules/**
- .git/**
- dist/**
- build/**

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

katalint loads `katalint.yml` from the current working directory by default.
Use `--config PATH` to load a different file.

```yaml
version: 1
targets:
  agent_configs:
    - AGENTS.md
    - AGENTS.override.md
    - CLAUDE.md
    - .claude/agents/*.md
  task_packets:
    - .agent/tasks/**/*.md
    - docs/agent/tasks/**/*.md
  handoffs:
    - .agent/handoffs/**/*.md
    - docs/agent/handoffs/**/*.md
rules:
  KTL001:
    max_lines: 200
    max_bytes: 32768
    severity: warning
  KTL104:
    max_files_per_task: 5
    severity: warning
fail_on: error
baseline: katalint-baseline.json
ignore:
  - vendor/**
  - docs/archive/**
```

`fail_on: error` keeps warning findings visible without failing CI. Rule
settings can override severity and rule-specific numeric thresholds such as
`KTL001.max_lines` and `KTL104.max_files_per_task`.

## CI usage

GitHub Actions usage for a repository that installs katalint from its local
checkout:

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
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -e .
      - run: katalint check
```

This repository dogfoods that workflow in `.github/workflows/katalint.yml`.
Published-package consumers can use the same command after installing katalint
with their package manager.

For pre-commit, use the local hook shape in
`docs/examples/pre-commit-config.yaml`.

## Examples

The example task packets show the expected workflow-rule behavior:

```bash
katalint check docs/examples/bad-task.md
katalint check docs/examples/good-task.md
```

- `docs/examples/bad-task.md` is intentionally missing acceptance criteria and
  a verification command.
- `docs/examples/good-task.md` includes both and should produce no findings.

## Suppressions

Inline suppression format:

```markdown
<!-- katalint-disable KTL002: project intentionally documents style because no formatter exists -->
```

Suppressions must include a reason. Comments without a reason are ignored.

Baseline files can be created with:

```bash
katalint check --write-baseline katalint-baseline.json
```

Then pass `--baseline katalint-baseline.json` or set `baseline:` in
`katalint.yml` to filter known findings during incremental adoption.

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
  32 KiB project guidance cap. Verified on 2026-07-07:
  https://developers.openai.com/codex/guides/agents-md
- Claude Code documents CLAUDE.md memory behavior and recommends specific,
  concise instructions. Verified on 2026-07-07:
  https://docs.anthropic.com/en/docs/claude-code/memory
- Claude Code documents project and user subagents as Markdown files with YAML
  frontmatter. Verified on 2026-07-07:
  https://docs.anthropic.com/en/docs/claude-code/sub-agents
- arXiv:2606.15828v2, "Configuration Smells in AGENTS.md Files: Common
  Mistakes in Configuring Coding Agents", catalogues six configuration smells
  for AGENTS.md and CLAUDE.md files. Verified on 2026-07-07; arXiv lists v2 as
  dated 2026-06-16:
  https://arxiv.org/abs/2606.15828
