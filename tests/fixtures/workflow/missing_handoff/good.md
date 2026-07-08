---
type: handoff
---

# Handoff: parser nested-list fix

## Changed Files

- src/katalint/parser.py
- tests/rules/test_parser.py

## Commands Run

```
pytest tests/rules/test_parser.py
```

## Test Results

All 42 tests passed, including the new nested-list regression test.

## Remaining Risks

Deeply nested ordered lists (depth > 6) are untested; behavior there is
unverified but unlikely in practice.

## Next Action

Rebase onto main and open the pull request for review.
