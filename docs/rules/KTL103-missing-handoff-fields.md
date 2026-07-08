# KTL103: Missing Handoff Fields

## Summary

Handoff documents should record what changed, how it was verified, and what
happens next so the next agent or reviewer can pick up work without
re-deriving context. KTL103 reports handoff documents that are missing one or
more of the 5 required fields.

## Category

workflow

## Default severity

error

## Applies to

Handoff documents, classified by `type: handoff` frontmatter. Discovery reads
the frontmatter (not the path) to decide a document's kind, so a file needs
`type: handoff` to be linted by this rule. Handoff files typically live under:

- `.agent/handoffs/**/*.md`
- `docs/agent/handoffs/**/*.md`

Note: a file placed in a handoff path but WITHOUT `type: handoff` frontmatter is
currently classified as `unknown` by discovery, so this handoff-only rule will
not run on it. Closing that path-vs-frontmatter gap is deferred to a separate
discovery-adjustment change and tracked independently.

## Accepted section headings

- `## Changed Files` / `## 変更ファイル`
- `## Commands Run` / `## 実行コマンド`
- `## Test Results` / `## テスト結果`
- `## Remaining Risks` / `## 残リスク` / `## 残存リスク`
- `## Next Action` / `## 次のアクション` / `## 次アクション`

## Rationale

A handoff is the interface between one unit of work and the next. Changed files
show where to inspect the diff, commands run and test results show how the work
was verified, remaining risks keep uncertainty visible, and the next action
prevents follow-up work from being silently dropped. When any of these are
omitted, the receiving agent or reviewer has to reconstruct context from diffs
and guesswork.

KTL103 is an error by default because incomplete handoffs directly weaken
deterministic CI and review workflows: a reviewer cannot confirm a change is
safe if the verification steps and residual risks were never written down.

## Bad

```markdown
# Handoff: config loader refactor

## Changed Files

- src/katalint/config.py

## Next Action

Someone should double-check the new defaults.
```

## Good

```markdown
# Handoff: config loader refactor

## Changed Files

- src/katalint/config.py
- src/katalint/cli.py

## Commands Run

python -m katalint check .

## Test Results

All tests passed, including new config fixtures.

## Remaining Risks

Windows path handling is untested.

## Next Action

Rebase onto main and open the pull request.
```

## Detection

v0 scans Markdown ATX headings for the accepted section names, matching each
heading's full text case-insensitively against the accepted aliases. It does
not attempt to judge whether the content under each section is complete or
correct.

## Suggested remediation

- Add a section for each missing required field using an accepted heading form.
- Prefer the standard `##` heading forms so tooling can detect them reliably.
- Record concrete verification details (commands and results), not just intent.
- Note any residual risk explicitly, even if it is "none known".

## Known limitations (v0)

Detection is line-based, not a full CommonMark parser. Standard fenced code
blocks (``` and ~~~, three markers) and closing ATX hashes are handled, but
some exotic Markdown is only approximated and may rarely be mis-scanned:
fences longer than three markers, indented (4-space) code blocks, and
info-string edge cases. This is accepted for v0 and can be tightened later.
