---
type: task
id: GOOD-EXAMPLE
---

# Fix Parser Error Path

## Goal

Handle the parser error path described by the failing fixture.

## Acceptance Criteria

- The parser returns a structured error for the malformed input fixture.
- The CLI keeps the same exit code for valid input.

## Verification

- `pytest -q tests/test_discovery.py`
