# KTL102 — Missing Verification Command

## Summary

Flags a task packet that does not provide a verification command or an explicit
verification-oriented section.

## Category

`workflow`

## Default severity

`error`

## Applies to

Task packets only. Handoff and config documents are not checked by this rule.

## Accepted headings and command vocabulary

A task packet passes if it contains an ATX Markdown heading whose text matches
one of these headings case-insensitively after the leading `#` markers are
stripped:

- `Verification`
- `Commands to run`
- `How to test`
- `Testing`
- `検証`
- `コマンド`

A task packet also passes if it names a recognized command, case-insensitively.
The vocabulary is split into two groups so that ordinary prose does not falsely
satisfy the rule:

Unambiguous commands are credited wherever they appear (they do not occur
incidentally in prose):

- `pytest`
- `npm test`
- `npm run`
- `yarn test`
- `make test`
- `go test`
- `cargo test`
- `mvn test`
- `./gradlew`

Generic single words are credited only when they appear in a command context --
inside a fenced code block, an inline code span (`` `...` ``), or on a shell
(`$`-prefixed) line -- never as a bare word in prose:

- `build`
- `lint`
- `tsc`
- `typecheck`

For example, a task titled `# Build the signup page` with no verification
section is still flagged, because `build` is only prose there. `` Run `tsc
--noEmit` `` or a `pytest` line inside a code block passes.

## Rationale

Task packets should explain how the completed work can be checked. Without a
verification section or a recognizable command, reviewers and implementers have
no clear way to confirm that the requested change is complete.

## Bad

```markdown
---
type: task
---

# Update the greeting copy

Change the welcome message shown on the home page so that it greets returning
visitors by name.

## Details

The current message is generic. Product would like a warmer tone that
acknowledges people who have signed in before.

## Notes

Keep the wording short and friendly. Coordinate with the design crew on the
final phrasing before merging.
```

## Good

````markdown
---
type: task
---

# Update the greeting copy

Change the welcome message shown on the home page so that it greets returning
visitors by name.

## Commands to run

```bash
pytest -q tests/test_greeting.py
```

Run the command above and confirm every check passes before you submit.
````

## Detection

1. Read the file as bytes. If the file cannot be read, emit no findings.
2. Decode the content with `errors="replace"`.
3. Scan each line for Markdown ATX headings, tracking fenced code blocks so
   that headings inside a code fence are ignored. For heading lines, strip the
   leading `#` markers, any optional closing `#` sequence, and surrounding
   whitespace, then compare the remaining text case-insensitively against the
   accepted verification headings.
4. Credit an unambiguous command if its substring appears anywhere in the
   decoded text, case-insensitively.
5. Credit a generic command word only if it appears inside a command context
   (a fenced code block, an inline code span, or a `$`-prefixed shell line).
6. If neither a verification heading nor a credited command is present, emit one
   finding at line 1. Otherwise, emit no findings.

## Suggested remediation

Add a `Commands to run` or `Verification` section with at least one runnable
test, lint, or build command, such as `pytest -q`, so the task can be verified
before it is considered done.

## Known limitations (v0)

Detection is line-based, not a full CommonMark parser. Standard fenced code
blocks (``` and ~~~, three markers) and closing ATX hashes are handled, but
some exotic Markdown is only approximated and may rarely be mis-scanned:
fences longer than three markers, indented (4-space) code blocks, and
info-string edge cases. This is accepted for v0 and can be tightened later.
