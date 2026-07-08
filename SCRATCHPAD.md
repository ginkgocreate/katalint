# SCRATCHPAD

## Completed Tasks

- Created the katalint project directory as a new Git repository.
- Created the PR-0 scope documentation scaffold.
- Added documentation contract tests for the PR-0 acceptance conditions.
- Verified PR-0 docs with `python3 -m unittest discover -s tests`.
- Verified whitespace with `git diff --check`.
- Committed the initial PR-0 scope work on `feature/pr-0-scope-docs`.
- Attempted `git push origin feature/pr-0-scope-docs`; it failed because no
  `origin` remote is configured.
- Merged PR #10, integrating PR1.1 discovery robustness, config rules KTL001-KTL003,
  and workflow rules KTL101-KTL104 into `main`.

## Findings

- The parent `/Users/user/work` directory is not a Git repository.
- katalint did not previously exist under `/Users/user/work`.
- arXiv:2606.15828 exists on arXiv as `2606.15828v2 [cs.SE]`, dated
  2026-06-16. The README reference was updated with verification status.
- PR-0 required scope: 5 documentation files.
- Process additions: 1 scratchpad and 1 contract test.
- Total committed files for PR-0: 7 files.
- Name availability spot check on 2026-07-07: PyPI returned no matching
  distribution for `katalint`; npm returned 404 for `katalint`; GitHub search
  found no exact `katalint` repository, only the nearby `mbbo128/katalinter`.
  Name reservation is still a human-gated action.
- `origin` is now configured as `https://github.com/ginkgocreate/katalint.git`.
- PR3.4 was not merged because it changes KTL004 from the locked
  `Init Fossilization` rule to `Prohibition Overload`.

## Next Actions

- Decide whether `Prohibition Overload` should become a later config rule under a
  new ID, or be dropped.
- Implement the locked KTL004 `Init Fossilization` rule, or explicitly revise the
  v0 rule catalogue.
- Start PR-5: configuration, suppressions, and baseline once KTL004 is resolved.

## Stocked Issues

- [QUESTION] PR3.4 implements `Prohibition Overload` as KTL004, but the locked
  v0 catalogue defines KTL004 as `Init Fossilization`.
