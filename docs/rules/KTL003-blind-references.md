# KTL003: Blind References

## Summary

Agent configuration files sometimes point an agent at unnamed prior art —
"follow the existing pattern," "as before," "the current approach" — without
saying where that prior art actually lives. An agent with no memory of the
repository's history has no way to resolve these references, and will either
guess or invent behavior that was never intended. KTL003 reports vague
references that have no concrete anchor (a URL, file path, section reference,
or inline explanation) nearby.

## Category

config

## Default severity

warning

## Applies to

Agent config files (AGENTS.md, AGENTS.override.md, CLAUDE.md,
.claude/agents/\*.md, and similar persistent instruction files).

## Default vocabulary

| Setting | Default |
| --- | --- |
| `VAGUE_PHRASES` | "the existing process", "existing style", "the style guide", "previous implementation", "as before", "the usual way", "follow the existing pattern", "the current approach", "like we did before", "既存の", "従来通り", "これまで通り", "いつもの" |

A line is only flagged when it contains one of these phrases (case-insensitive
substring match) AND none of the lines in its immediate window (the line
itself, the line before, and the line after) contain a concrete anchor: an
`http(s)://` URL, a markdown link (`[text](target)`), a backticked path or
filename, a bare `word/word` path, a known file extension (`.md`, `.py`,
`.ts`, etc.), the word "section" or a `§`/`##` marker, or an explanatory
clause ("because", "for example", "e.g.", "i.e.", "namely", "specifically").

## Rationale

Instructions that say "do it the way we did before" are only useful to a
reader who already knows what "before" means. For a human maintainer that
might be recoverable from memory or `git blame`; for an agent operating from
the text of the file alone, it is not. Requiring a nearby link, path,
section reference, or explanation turns an implicit tribal-knowledge pointer
into something the agent (and the next human) can actually follow.

## Bad

```markdown
## Coding style

Just follow the existing pattern when writing new code.

## Testing

Run the tests as before.
```

Neither vague reference has a URL, path, section, or explanation nearby, so
an agent reading this file has no way to find "the existing pattern" or what
was done "before."

## Good

```markdown
## Coding style

Follow the existing pattern documented in `docs/style-guide.md`. It covers
naming, formatting, and import ordering.

## Testing

As before, run `pytest` locally and see https://example.com/ci/testing for
the CI matrix.
```

Each vague phrase is immediately anchored to a concrete path, URL, or
section, so the reference resolves without prior context.

## Detection

v0 scans each physical line of the file for a case-insensitive substring
match against `VAGUE_PHRASES`. For each matching line, it builds a window of
up to three physical lines (the previous line, the line itself, and the next
line) and checks that window for a concrete anchor. If no anchor is found in
the window, one `Finding` is emitted with `line` set to the actual 1-based
line number of the vague reference (not `1`, unlike whole-file rules such as
KTL001). A single line that matches more than one vague phrase still
produces at most one finding for that line.

The anchor patterns are deliberately broad — a bare `word/word` token, for
example, is treated as a path even though it will occasionally match
something that is not really a path (e.g. "and/or"). This is intentional:
the rule is tuned to avoid false positives on legitimate concrete references
at the cost of occasionally missing a borderline blind reference.

## Suggested remediation

- Replace "the existing process" or "as before" with a link to the actual
  document, PR, or ADR being referenced.
- Point to a specific file path or section heading instead of an unnamed
  prior implementation.
- If there is no durable place to point to, write the process out inline
  instead of gesturing at it.
