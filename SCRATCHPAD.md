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
- Implemented locked KTL004 `Init Fossilization` on
  `feature/pr3.4-init-fossilization`.
- Implemented PR-5 configuration, inline suppressions, and baseline support on
  `feature/pr5-config-suppressions-baseline`.
- Started PR-6 CI integration, dogfooding files, and examples on
  `feature/pr6-ci-dogfooding-examples`.
- Started v0.1.0 release-readiness finish on `release/v0.1.0-readiness`.

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
- The earlier `feature/pr3.4-prohibition-overload` branch was not merged because
  it changes KTL004 from the locked
  `Init Fossilization` rule to `Prohibition Overload`.
- KTL004 `Init Fossilization` uses Git history only: AGENTS.md/CLAUDE.md,
  tracked files, repository commits >= 8, and file commits <= 1.
- PR-5 loads `katalint.yml`, supports `fail_on`, custom targets, ignore globs,
  rule severity/options, reason-required inline suppressions, and JSON baseline
  read/write.
- PR-6 dogfooding uses `fail_on: error` so warnings remain visible without
  blocking incremental adoption.
- v0.1.0 finish promotes the runtime version from `0.1.0a1` to `0.1.0`, adds
  MIT licensing, changelog, package metadata, package rule docs, and CI build
  validation.

## Next Actions

- Decide whether `Prohibition Overload` should become a later config rule under a
  new ID, or be dropped.
- Open and merge the v0.1.0 release-readiness PR once review/CI passes.
- Create the `v0.1.0` tag after the release-readiness PR is on `main`.
- Publish to PyPI only after a human provides package-owner credentials.

## Stocked Issues

- [QUESTION] The earlier `feature/pr3.4-prohibition-overload` branch implements
  `Prohibition Overload` as KTL004, but the locked v0 catalogue defines KTL004
  as `Init Fossilization`. Decide whether Prohibition Overload gets a later ID.
