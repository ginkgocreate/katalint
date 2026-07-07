---
type: task
---

# Modernize logging

Update modules under `src/**` to use the structured logging format introduced
last quarter. Start with the request handlers and work outward.

## Notes

- Prefer the `structlog` wrapper over the standard library logger.
- Keep log messages single-line.

## Acceptance Criteria

- Modules under the source tree emit structured logs.
- Existing tests still pass.
