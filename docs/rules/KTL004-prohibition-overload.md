# KTL004: Prohibition Overload

## Summary

Persistent agent instruction files should tell an agent what to do, not just
what not to do. KTL004 reports config files that are dominated by
prohibitions ("never", "do not", ...) with too few positive, actionable
"must-do" instructions to balance them.

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
| `max_prohibitions` | 5 |
| `min_must_do_ratio` | 0.5 |

## Rationale

A config file that is mostly a list of forbidden actions is hard to act on:
an agent can infer many things it should not do, but has no positive signal
for what a correct action looks like. Balancing prohibitions with concrete
"must do" instructions makes the file both more useful and easier to verify.

## Detection

v0 counts case-insensitive occurrences of a fixed set of prohibition markers
(`NEVER`, `DO NOT`, `DON'T`, `MUST NOT`, `SHALL NOT`, `禁止`, `絶対に`,
`してはいけない`, `するな`) and a fixed set of must-do markers (`MUST`,
`ALWAYS`, `SHOULD`, `DO`, `REQUIRED`, `してください`, `すること`, `必ず`)
across the whole file.

ASCII markers are matched with word boundaries, so marker text embedded in a
larger word never false-matches: `must notify`, `do notify`, `document`,
`mustard`, and `shoulder` do not count, while the real phrases `MUST NOT` and
`DO NOT` still do. The Japanese markers have no word boundaries and use plain
substring matching.

The `MUST` and `DO` must-do markers are never counted when they head a
`MUST NOT` or `DO NOT` prohibition (i.e. followed by the whole word `not`), so
a prohibition is never also credited as a must-do instruction. A positive
`must notify` or `do notify` still counts as a must-do.

```
must_do_ratio = must_do_count / (must_do_count + prohibition_count)
```

A finding fires only when both of the following hold:

- `prohibition_count` is strictly greater than `max_prohibitions` (5)
- `must_do_ratio` is strictly less than `min_must_do_ratio` (0.5)

If there are no prohibition or must-do markers at all, there is nothing to
compare and no finding is produced.

## Bad

```markdown
- Never push directly to main.
- Never skip code review.
- Never disable CI checks.
- Do not commit generated files.
- Do not modify vendored dependencies.
- Don't rename public APIs without approval.
- Don't touch the release pipeline manually.
- Shall not bypass the approval workflow.
```

Eight prohibitions, zero must-do instructions: `must_do_ratio` is `0.00`,
well below the `0.5` threshold, so this fires.

## Good

```markdown
- You must run the test suite before committing.
- Always keep pull requests scoped to a single change.
- You should document new environment variables in README.md.
- Required: every new endpoint needs an integration test.
- Never commit secrets or API keys to the repository.
- Don't merge without at least one review.
```

Only two prohibitions here -- below the `max_prohibitions` threshold on its
own, regardless of ratio -- so this does not fire.

## Suggested remediation

- Rewrite key prohibitions as positive, testable "do" instructions.
- Move exhaustive prohibition lists to a separate reference document.
- Keep the root instruction file focused on what to do, using a handful of
  the most important prohibitions as guardrails rather than an exhaustive
  ban list.
