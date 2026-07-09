# KTL002: Lint Leakage

## Summary

KTL002 flags agent guidance files (such as `AGENTS.md`) that **duplicate
prescriptive lint/format/style rules** which a neighbouring formatter or linter
config already enforces. The rule uses a conservative discriminator: it fires
only when the file restates concrete, prescriptive style *directives* (for
example "use 4 spaces for indentation" or "max line length 88 characters") AND a
recognised config file lives in the same directory. Files that merely mention or
**delegate** to tooling ("linting is enforced by project tooling", "see
`ruff.toml`", "run the linter") are the recommended good pattern and do **not**
fire.

## Category

config

## Default severity

warning

## Applies to

- AGENTS.md
- AGENTS.override.md
- CLAUDE.md
- .claude/agents/*.md

## Prescriptive style directives

The rule detects concrete rules via a class-level `ClassVar` tuple of
`(label, regex_pattern)` pairs, matched case-insensitively:

```python
STYLE_DIRECTIVES: ClassVar[tuple[tuple[str, str], ...]] = (
    ("indentation width", r"\b\d+[\s-]?spaces?\b"),
    ("indentation width", r"\b(?:use\s+)?tabs?\s+for\s+indent"),
    ("line length", r"\bline[\s-]?length\b[^.\n]{0,15}\d+"),
    ("line length", r"\b\d+\s*(?:characters?|chars?|columns?|cols?)\b"),
    ("trailing whitespace", r"\b(?:no|never|remove|strip|trim|avoid)\b[^.\n]{0,30}trailing\s+whitespace\b"),
    ("semicolons", r"\b(?:always|never|no|add|omit|require)\b[^.\n]{0,20}semicolons?\b"),
    ("quote style", r"\b(?:single|double)\s+quotes?\b"),
)
```

Each label names a concrete rule a formatter enforces:

- **indentation width** -- the exact indentation the formatter applies (spaces
  count or tabs), e.g. "4 spaces" / "use tabs for indent".
- **line length** -- the maximum line width the linter enforces, e.g. "line
  length 88" or "88 characters".
- **trailing whitespace** -- prohibiting/stripping trailing whitespace, which
  the formatter handles automatically.
- **semicolons** -- rules about always/never adding semicolons, owned by the
  formatter.
- **quote style** -- single vs double quote preference, owned by the formatter.

## Config filenames

```python
CONFIG_FILENAMES: ClassVar[tuple[str, ...]] = (
    ".prettierrc",
    ".prettierrc.json",
    "prettier.config.js",
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.json",
    "eslint.config.js",
    ".flake8",
    "ruff.toml",
    ".ruff.toml",
    "pyproject.toml",
    ".rubocop.yml",
)
```

## Rationale

Prescriptive rules copied into guidance files drift away from the real config,
which is the actual source of truth. Over time the duplicated numbers and
directives go stale and contradict what the tooling enforces, confusing both
humans and agents. Delegating to the config file is the correct pattern and must
**not** be flagged -- the earlier version of this rule wrongly punished exactly
that good pattern, and this revision fixes that false positive.

### Known limitation: pyproject.toml is presence-only

The `pyproject.toml` check is **presence-only**: KTL002 does not inspect whether
a relevant `[tool.*]` section is actually configured. It is not TOML-section
aware, so a `pyproject.toml` with no linter/formatter section still counts toward
condition (b).

## Bad

An `AGENTS.md` that restates concrete rules already owned by a sibling
`ruff.toml`:

```markdown
# Backend Agent Guide

## Code style

Keep the maximum line length at 88 characters, use 4-space indentation, and
never leave trailing whitespace in Python files.
```

(sitting next to a real `ruff.toml` in the same directory)

## Good

An `AGENTS.md` that delegates to the tooling instead of restating rules:

```markdown
# Frontend Agent Guide

Formatting and linting are enforced by project tooling; see `ruff.toml` and
`.eslintrc` instead of restating the rules. Run the linter before committing.
```

This passes even when the config file is present in the same directory, because
it contains no prescriptive style directive.

## Detection

Both conditions are required (logical AND):

(a) At least one prescriptive `STYLE_DIRECTIVE` regex matches the file text.
    Bare mentions of, or delegation to, tooling do NOT match and do NOT fire.

(b) A file named in `CONFIG_FILENAMES` exists in `file.parent`.

When both hold, exactly one warning is emitted per `check()` call (never one per
directive, never one per config file). Unreadable or missing files return `[]`
without raising.

The `line length` directive additionally requires line-length context: a numeric
character or column count (for example `80 characters`) only counts when it
appears near a line-context word such as `line`, `row`, `width`, `行`, `桁`, or
`列幅`, or in the explicit phrase `line length` / `line width`. A bare count with
no line context (for example an ops rule like "Keep PR summaries under 500
characters") does not match.

## Known limitations (v0)

Prescriptive-directive detection is heuristic. It may miss unusual phrasings of a
real style rule, and it may (rarely) match an operational rule that happens to
resemble a style directive. The `pyproject.toml` check is presence-only and is
not TOML-section aware. These heuristics are intended to be conservative and may
be tightened in a later revision.

## Suggested remediation

Remove the duplicated prescriptive lint/format rules from the guidance file and
defer to the formatter/linter config (for example `ruff.toml` or `.prettierrc`)
as the single source of truth. If context is helpful, link to the config file
rather than restating its individual rules.
