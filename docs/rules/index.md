# Rule catalogue

katalint rule IDs use the `KTL` prefix.

| Number range | Use |
| --- | --- |
| KTL001-KTL099 | Configuration smells |
| KTL101-KTL199 | Workflow smells |
| KTL201-KTL299 | Future security and repository policy rules |
| KTL901-KTL999 | Deprecated and compatibility rules |

## v0 active rules

| Rule | Category | Name | Applies to | Default | Deterministic signal |
| --- | --- | --- | --- | --- | --- |
| KTL001 | config | Context Bloat | AGENTS.md, AGENTS.override.md, CLAUDE.md, .claude/agents/*.md | warning | line count and byte count |
| KTL002 | config | Lint Leakage | agent config files | warning | lint, format, and style vocabulary plus existing config files |
| KTL003 | config | Blind References | agent config files | warning | vague references without nearby URL, path, or explanation |
| KTL004 | config | Prohibition Overload | AGENTS.md, AGENTS.override.md, CLAUDE.md, .claude/agents/*.md | warning | prohibition count and must-do ratio |
| KTL101 | workflow | Missing Acceptance Criteria | task packets | error | missing accepted section aliases |
| KTL102 | workflow | Missing Verification Command | task packets | error | missing verification section or command vocabulary |
| KTL103 | workflow | Missing Handoff Fields | handoff documents | error | required handoff fields absent |
| KTL104 | workflow | Scope Too Wide | task packets | warning | broad globs, broad directories, or repo-wide wording |

## Reserved rules

| Rule | Category | Name | Reason reserved |
| --- | --- | --- | --- |
| KTL005 | config | Skill Leakage | Regex-only detection is likely to be noisy |
| KTL006 | config | Conflicting Instructions | Requires semantic comparison |
| KTL105 | workflow | Judgment / Execution Mixed | Requires semantic comparison |

## Default severity policy

Configuration smells default to warnings in v0. They identify reliability risk,
but they should not block adoption on the first run.

Workflow smells can default to errors when a missing field directly weakens
task execution or handoff quality. Missing acceptance criteria, verification
commands, and handoff fields are errors by default. Scope breadth remains a
warning in v0 because broad work can be intentional.

## Output contract

Every finding should include:

```json
{
  "rule_id": "KTL001",
  "category": "config",
  "severity": "warning",
  "file": "AGENTS.md",
  "line": 1,
  "message": "AGENTS.md has 236 lines.",
  "suggestion": "Move task-specific instructions to separate docs or skills."
}
```

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | No findings above the configured failure threshold |
| 1 | Lint finding above the configured failure threshold |
| 2 | CLI or configuration usage error |
| 3 | Internal error |
