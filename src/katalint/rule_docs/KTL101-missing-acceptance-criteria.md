# KTL101: Missing Acceptance Criteria

## Summary

Task packets should define what "done" means before an agent starts work.
KTL101 reports task documents that do not include an acceptance criteria section
or an accepted alias.

## Category

workflow

## Default severity

error

## Applies to

- docs/tasks/**/*.md
- .katalint/tasks/**/*.md
- issue packets
- task packets

## Accepted section headings

- `## Acceptance Criteria`
- `## Done When`
- `## Definition of Done`
- `## 完了条件`
- `## 受け入れ条件`

## Rationale

Without acceptance criteria, an agent has to infer completion from prose. That
raises the chance of under-scoped fixes, over-scoped rewrites, or handoffs that
cannot be verified by a reviewer.

KTL101 is an error by default because missing completion criteria directly
weakens deterministic CI and review workflows.

## Bad

```markdown
# Fix parser

The parser fails on nested lists. Please clean it up.
```

## Good

```markdown
# Fix parser

The parser fails on nested lists.

## Acceptance Criteria

- Nested lists parse without dropping child items.
- Existing flat-list fixtures still pass.
- The fix includes a regression test.
```

## Detection

v0 scans Markdown headings for the accepted section names. It does not attempt
to judge whether the listed criteria are good enough.

## Suggested remediation

- Add a clear acceptance criteria section.
- Prefer observable outcomes over implementation wishes.
- Include at least one verification-oriented criterion when possible.

## Known limitations (v0)

Detection is line-based, not a full CommonMark parser. Standard fenced code
blocks (``` and ~~~, three markers) and closing ATX hashes are handled, but
some exotic Markdown is only approximated and may rarely be mis-scanned:
fences longer than three markers, indented (4-space) code blocks, and
info-string edge cases. This is accepted for v0 and can be tightened later.
